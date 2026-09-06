// SPDX-License-Identifier: MIT
#include "ShaderJit.hpp"
#include "AirDecoder.hpp"

#include <algorithm>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <utility>

namespace MellowRT { namespace ShaderJit {
namespace {

struct Failure : std::runtime_error { using std::runtime_error::runtime_error; };
struct Token {
    std::string text;
    size_t line = 1, column = 1;
    bool quoted = false;
};

bool alpha(char c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_'; }
bool digit(char c) { return c >= '0' && c <= '9'; }
bool hex(char c) { return digit(c) || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'); }
bool identifier(const std::string &s) {
    return !s.empty() && alpha(s[0]) && std::all_of(s.begin() + 1, s.end(), [](char c) { return alpha(c) || digit(c); });
}

std::vector<Token> lex(const std::string &source, bool air) {
    if (source.empty() || source.size() > MaxSourceBytes) throw Failure("Source size must be 1..65536 bytes");
    for (unsigned char c : source) if (c == 0 || c > 127) throw Failure("NUL and non-ASCII source are unsupported");
    std::vector<Token> tokens;
    size_t pos = 0, line = 1, col = 1;
    auto advance = [&]() { if (source[pos++] == '\n') { ++line; col = 1; } else { ++col; } };
    while (pos < source.size()) {
        char c = source[pos];
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') { advance(); continue; }
        if ((air && c == ';') || (!air && source.compare(pos, 2, "//") == 0)) {
            while (pos < source.size() && source[pos] != '\n') advance();
            continue;
        }
        if (!air && source.compare(pos, 2, "/*") == 0) {
            advance(); advance();
            while (pos < source.size() && source.compare(pos, 2, "*/") != 0) advance();
            if (pos == source.size()) throw Failure("Unterminated block comment");
            advance(); advance(); continue;
        }
        Token token; token.line = line; token.column = col;
        size_t start = pos;
        if (alpha(c) || (air && c == '.')) {
            do { advance(); } while (pos < source.size() && (alpha(source[pos]) || digit(source[pos]) || (air && source[pos] == '.')));
        } else if (digit(c)) {
            if (!air && source.compare(pos, 2, "0x") == 0) {
                advance(); advance();
                if (pos == source.size() || !hex(source[pos])) throw Failure("Malformed hexadecimal literal");
                while (pos < source.size() && hex(source[pos])) advance();
            } else {
                do { advance(); } while (pos < source.size() && digit(source[pos]));
            }
            if (!air && pos < source.size() && (source[pos] == 'u' || source[pos] == 'U')) advance();
        } else if (air && c == '"') {
            token.quoted = true;
            advance(); start = pos;
            while (pos < source.size() && source[pos] != '"') {
                if (source[pos] == '\\' || source[pos] == '\n' || source[pos] == '\r') throw Failure("Escaped/multiline LLVM strings are unsupported");
                advance();
            }
            if (pos == source.size()) throw Failure("Unterminated LLVM string");
            token.text = source.substr(start, pos - start); advance();
        } else {
            const std::string permitted = air ? "@%!#={}(),<>*:-+[]" : "#<>[]{}()*+-/%&|^~;,=";
            if (permitted.find(c) == std::string::npos) throw Failure("Unsupported character at " + std::to_string(line) + ":" + std::to_string(col));
            advance();
            if (!air && pos < source.size()) {
                const std::string pair = source.substr(start, 2);
                static const std::set<std::string> pairs = {"<<", ">>", "++", "--", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "==", "<=", ">=", "&&", "||"};
                if (pairs.count(pair)) {
                    advance();
                    if ((pair == "<<" || pair == ">>") && pos < source.size() && source[pos] == '=') advance();
                }
            }
        }
        if (!token.quoted) token.text = source.substr(start, pos - start);
        tokens.push_back(std::move(token));
        if (tokens.size() > MaxTokens) throw Failure("Token budget exceeded");
    }
    tokens.push_back(Token{"", line, col, false});
    return tokens;
}

class Tokens {
protected:
    explicit Tokens(const std::string &s, bool air = false) : tokens_(lex(s, air)) {}
    const Token &peek() const { return tokens_[position_]; }
    bool at(const std::string &text) const { return !peek().quoted && peek().text == text; }
    bool take(const std::string &text) { if (!at(text)) return false; if (!text.empty()) ++position_; return true; }
    [[noreturn]] void fail(const std::string &message) const {
        throw Failure(std::to_string(peek().line) + ":" + std::to_string(peek().column) + ": " + message);
    }
    void require(const std::string &text) { if (!take(text)) fail("Expected '" + text + "'"); }
    std::string name() {
        if (peek().quoted || !identifier(peek().text)) fail("Expected an identifier");
        return tokens_[position_++].text;
    }
    std::string quoted() { if (!peek().quoted) fail("Expected a string"); return tokens_[position_++].text; }
    std::string consume() { if (at("")) fail("Unexpected end of input"); return tokens_[position_++].text; }
    uint64_t decimal(uint64_t maximum) {
        if (peek().quoted || peek().text.empty()) fail("Expected a decimal integer");
        uint64_t value = 0;
        for (char c : peek().text) {
            if (!digit(c) || value > (maximum - static_cast<unsigned>(c - '0')) / 10u || static_cast<unsigned>(c - '0') > maximum)
                fail("Decimal integer outside supported range");
            value = value * 10u + static_cast<unsigned>(c - '0');
        }
        ++position_; return value;
    }
    std::vector<Token> tokens_;
    size_t position_ = 0;
};

enum class Scalar { Int, UInt };
enum class NodeKind { Literal, Symbol, Load, Unary, Binary };
struct Node {
    NodeKind kind;
    Scalar type = Scalar::UInt;
    uint32_t value = 0;
    bool constant = false;
    bool exactIndex = false;
    size_t symbol = 0;
    size_t height = 1;
    std::string op;
    std::unique_ptr<Node> left, right;
};
using Expr = std::unique_ptr<Node>;
struct Symbol { std::string source, emitted; bool immutable = false, exactIndex = false; };
struct Statement { bool declaration = false, constant = false, buffer = false; size_t symbol = 0; Expr expression; };

const std::set<std::string> &reserved() {
    static const std::set<std::string> words = {
        "kernel", "void", "device", "uint", "int", "float", "half", "bool", "const", "return", "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "using", "namespace", "metal", "thread", "threadgroup", "constant", "volatile", "atomic_uint", "auto", "struct", "class", "typedef", "sizeof", "true", "false", "__kernel", "__global", "global", "local", "private", "read_only", "write_only", "unsigned", "signed", "long", "short", "char", "double", "sampler_t", "size_t", "event_t", "get_global_id",
        "alignas", "alignof", "and", "and_eq", "asm", "bitand", "bitor", "catch", "char16_t", "char32_t", "compl", "concept", "const_cast", "constexpr", "consteval", "constinit", "co_await", "co_return", "co_yield", "decltype", "default", "delete", "dynamic_cast", "enum", "explicit", "export", "extern", "friend", "goto", "inline", "mutable", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq", "protected", "public", "register", "reinterpret_cast", "requires", "restrict", "static", "static_assert", "static_cast", "template", "this", "thread_local", "throw", "try", "typeid", "typename", "union", "virtual", "wchar_t", "xor", "xor_eq"
    };
    return words;
}

class MslParser : Tokens {
public:
    MslParser(const std::string &source, const std::string &entry) : Tokens(source), entry_(entry) {}
    CompileResult run() {
        if (!identifier(entry_) || reserved().count(entry_) || entry_[0] == '_') fail("Unsupported entry identifier");
        if (take("#")) { require("include"); require("<"); require("metal_stdlib"); require(">"); }
        if (take("using")) { require("namespace"); require("metal"); require(";"); }
        require("kernel"); require("void");
        if (name() != entry_) fail("Requested entry does not match the single kernel");
        require("(");
        for (size_t arg = 0; arg < 2; ++arg) {
            if (arg) require(",");
            if (take("device")) {
                if (!bufferName_.empty()) fail("Exactly one device uint buffer is supported");
                require("uint"); require("*"); bufferName_ = declaredName();
                require("["); require("["); require("buffer"); require("(");
                if (decimal(31) != 0) fail("Only buffer(0) is supported");
                require(")"); require("]"); require("]");
            } else {
                require("uint");
                if (!threadName_.empty()) fail("Exactly one scalar thread index is supported");
                threadName_ = declaredName();
                require("["); require("["); require("thread_position_in_grid"); require("]"); require("]");
                symbols_.push_back(Symbol{threadName_, "mellow_gid", true, true});
            }
        }
        require(")");
        if (bufferName_.empty() || threadName_.empty()) fail("Kernel must have buffer(0) and thread_position_in_grid");
        require("{");
        while (!take("}")) statement();
        require("");
        if (!writes_) fail("Kernel must write at least one value to its current thread element");
        CompileResult result;
        result.reflection.entry = entry_;
        result.reflection.threadIndexName = threadName_;
        result.reflection.buffers.push_back(BufferBinding{bufferName_, 0, "uint", true});
        result.openclSource = "// Mellow typed MSL subset; host must enforce exact 1D dispatch.\n__kernel void " + entry_ + "(__global uint *mellow_buffer0) {\n  const uint mellow_gid = (uint)get_global_id(0);\n";
        for (const auto &s : statements_) {
            result.openclSource += "  ";
            if (s.declaration) result.openclSource += s.constant ? "const uint " : "uint ";
            result.openclSource += s.buffer ? "mellow_buffer0[mellow_gid]" : symbols_[s.symbol].emitted;
            result.openclSource += " = " + emit(*s.expression) + ";\n";
        }
        result.openclSource += "}\n";
        result.success = true;
        return result;
    }
private:
    std::string declaredName() {
        std::string value = name();
        if (reserved().count(value) || value[0] == '_' || value.compare(0, 7, "mellow_") == 0 || !names_.insert(value).second) fail("Reserved or duplicate identifier");
        return value;
    }
    Expr node(NodeKind kind) { if (++nodeCount_ > MaxAstNodes) fail("AST node budget exceeded"); auto n = std::make_unique<Node>(); n->kind = kind; return n; }
    size_t symbol(const std::string &name) const {
        for (size_t i = 0; i < symbols_.size(); ++i) if (symbols_[i].source == name) return i;
        fail("Unknown or uninitialized variable");
    }
    void index(size_t depth = 0) { require("["); auto i = expression(1, depth + 1); require("]"); if (!i->exactIndex) fail("Buffer index must be the immutable current thread index"); }
    void statement() {
        if (statements_.size() >= MaxStatements) fail("Statement budget exceeded");
        Statement s;
        s.constant = take("const");
        if (take("uint")) {
            s.declaration = true;
            auto n = declaredName();
            require("="); s.expression = expression(); require(";");
            s.symbol = symbols_.size();
            symbols_.push_back(Symbol{n, "mellow_v" + std::to_string(s.symbol), s.constant, s.constant && s.expression->exactIndex});
        } else {
            if (s.constant) fail("Only const uint local declarations are supported");
            auto n = name();
            if (n == bufferName_) { index(); s.buffer = true; ++writes_; }
            else { s.symbol = symbol(n); if (symbols_[s.symbol].immutable) fail("Cannot assign an immutable local or thread index"); }
            require("="); s.expression = expression(); require(";");
        }
        statements_.push_back(std::move(s));
    }
    static int precedence(const std::string &op) {
        if (op == "|") return 1;
        if (op == "^") return 2;
        if (op == "&") return 3;
        if (op == "<<" || op == ">>") return 4;
        if (op == "+" || op == "-") return 5;
        if (op == "*" || op == "/" || op == "%") return 6;
        return 0;
    }
    Expr expression(int minimum = 1, size_t depth = 0) {
        if (depth > MaxExpressionDepth) fail("Expression depth budget exceeded");
        Expr left = primary(depth + 1);
        while (precedence(peek().text) >= minimum) {
            const auto op = consume();
            auto right = expression(precedence(op) + 1, depth + 1);
            auto n = node(NodeKind::Binary); n->op = op; n->left = std::move(left); n->right = std::move(right);
            n->height = 1 + std::max(n->left->height, n->right->height);
            if (n->height > MaxExpressionDepth) fail("AST depth budget exceeded");
            validateBinary(*n); left = std::move(n);
        }
        return left;
    }
    Expr primary(size_t depth) {
        if (depth > MaxExpressionDepth) fail("Expression depth budget exceeded");
        if (take("(")) { auto n = expression(1, depth + 1); require(")"); return n; }
        if (at("+") || at("-") || at("~")) {
            auto n = node(NodeKind::Unary); n->op = consume(); n->left = primary(depth + 1); n->type = n->left->type;
            n->height = 1 + n->left->height;
            if (n->height > MaxExpressionDepth) fail("AST depth budget exceeded");
            if (n->op != "+" && n->type != Scalar::UInt) fail("Unary minus/complement requires uint");
            n->constant = n->left->constant;
            if (n->constant) n->value = n->op == "-" ? uint32_t(0u - n->left->value) : n->op == "~" ? ~n->left->value : n->left->value;
            return n;
        }
        if (!peek().text.empty() && digit(peek().text[0])) {
            auto n = node(NodeKind::Literal); std::string text = consume();
            bool suffix = text.back() == 'u' || text.back() == 'U'; if (suffix) text.pop_back();
            unsigned base = text.compare(0, 2, "0x") == 0 ? 16 : 10;
            if (base == 10 && text.size() > 1 && text[0] == '0') fail("Octal literals are unsupported");
            uint64_t value = 0;
            for (size_t i = base == 16 ? 2 : 0; i < text.size(); ++i) {
                char c = text[i]; unsigned d = digit(c) ? unsigned(c - '0') : unsigned((c | 32) - 'a' + 10);
                if (d >= base || value > (uint64_t(UINT32_MAX) - d) / base) fail("Literal exceeds uint32");
                value = value * base + d;
            }
            n->type = suffix || (base == 16 && value > INT32_MAX) ? Scalar::UInt : Scalar::Int;
            if (n->type == Scalar::Int && value > INT32_MAX) fail("Unsuffixed decimal exceeds supported int32");
            n->value = static_cast<uint32_t>(value); n->constant = true; return n;
        }
        auto nameValue = name();
        if (nameValue == bufferName_) { index(depth + 1); return node(NodeKind::Load); }
        auto n = node(NodeKind::Symbol); n->symbol = symbol(nameValue); n->exactIndex = symbols_[n->symbol].exactIndex; return n;
    }
    void validateBinary(Node &n) {
        const auto &a = *n.left, &b = *n.right;
        bool shift = n.op == "<<" || n.op == ">>";
        n.type = shift ? a.type : (a.type == Scalar::UInt || b.type == Scalar::UInt ? Scalar::UInt : Scalar::Int);
        if ((n.op == "/" || n.op == "%") && (!b.constant || b.value == 0)) fail("Division/remainder requires a nonzero constant divisor");
        if (shift && (!b.constant || b.value >= 32)) fail("Shift count must be a constant in 0..31");
        n.constant = a.constant && b.constant;
        if (!n.constant) return;
        const uint64_t av = a.value, bv = b.value;
        uint64_t v = 0;
        if (n.op == "+") v = av + bv;
        else if (n.op == "-") { if (n.type == Scalar::Int && av < bv) fail("Negative signed constant subexpressions are unsupported"); v = av - bv; }
        else if (n.op == "*") v = av * bv;
        else if (n.op == "/") v = av / bv;
        else if (n.op == "%") v = av % bv;
        else if (n.op == "&") v = av & bv;
        else if (n.op == "|") v = av | bv;
        else if (n.op == "^") v = av ^ bv;
        else if (n.op == "<<") v = av << bv;
        else if (n.op == ">>") v = av >> bv;
        if (n.type == Scalar::Int && v > INT32_MAX) fail("Signed constant subexpression overflow");
        n.value = static_cast<uint32_t>(v);
    }
    std::string emit(const Node &n) const {
        if (n.constant) return std::to_string(n.value) + (n.type == Scalar::UInt ? "u" : "");
        if (n.kind == NodeKind::Symbol) return symbols_[n.symbol].emitted;
        if (n.kind == NodeKind::Load) return "mellow_buffer0[mellow_gid]";
        if (n.kind == NodeKind::Unary) return "(" + n.op + emit(*n.left) + ")";
        return "(" + emit(*n.left) + " " + n.op + " " + emit(*n.right) + ")";
    }
    std::string entry_, bufferName_, threadName_;
    std::set<std::string> names_;
    std::vector<Symbol> symbols_;
    std::vector<Statement> statements_;
    size_t nodeCount_ = 0, writes_ = 0;
};

// AIR lowering intentionally uses an explicit SSA/metadata grammar. LLVM IR
// optimizations, intrinsics and poison-producing flags are not approximated.
enum class AirType { U32, Index64, Thread3, Pointer };
struct AirValue { AirType type; std::string emitted; bool exactIndex = false; bool elementPointer = false; };
struct Metadata {
    enum class Kind { Integer, String, Reference, Function, List } kind = Kind::List;
    uint32_t integer = 0;
    std::string text;
    std::vector<Metadata> list;
};

class AirParser : Tokens {
public:
    AirParser(const std::string &source, const std::string &entry) : Tokens(source, true), entry_(entry) {}
    CompileResult run() {
        if (!identifier(entry_) || reserved().count(entry_) || entry_[0] == '_') fail("Unsupported AIR entry identifier");
        if (take("source_filename")) { require("="); quoted(); }
        require("target"); require("datalayout"); require("=");
        const auto layout = quoted();
        // Observed in Apple metalfe AIR 2.7 output, not inferred from host ABI.
        if (layout != "e-p:64:64:64-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:64:64-f32:32:32-f64:64:64-v16:16:16-v24:32:32-v32:32:32-v48:64:64-v64:64:64-v96:128:128-v128:128:128-v192:256:256-v256:256:256-v512:512:512-v1024:1024:1024-n8:16:32")
            fail("AIR data layout is not the validated 64-bit AIR 2.7 layout");
        require("target"); require("triple"); require("=");
        const auto triple = quoted();
        const std::string prefix = "air64_v27-apple-macosx";
        if (triple.compare(0, prefix.size(), prefix) != 0 || triple.size() == prefix.size() || !digit(triple[prefix.size()]) ||
            !std::all_of(triple.begin() + static_cast<ptrdiff_t>(prefix.size()), triple.end(), [](char c) { return digit(c) || c == '.'; }))
            fail("Only AIR 2.7 macOS target triples are supported");
        require("define"); take("weak_odr"); require("void"); require("@");
        if (name() != entry_) fail("AIR requested entry mismatch");
        require("("); pointerType(); argumentDecorations(); bufferSsa_ = ssaName();
        require(",");
        if (take("<")) { require("3"); require("x"); require("i32"); require(">"); vectorThread_ = true; }
        else require("i32");
        take("noundef"); threadSsa_ = ssaName();
        if (threadSsa_ == bufferSsa_) fail("Duplicate AIR argument");
        require(")"); take("local_unnamed_addr");
        if (take("#")) functionAttributes_ = static_cast<int64_t>(decimal(UINT32_MAX));
        require("{");
        values_.emplace(bufferSsa_, AirValue{AirType::Pointer, "mellow_buffer0", false, false});
        values_.emplace(threadSsa_, AirValue{vectorThread_ ? AirType::Thread3 : AirType::U32, "mellow_gid", !vectorThread_, false});
        // A label is permitted only before the first instruction. No branches.
        if (position_ + 1 < tokens_.size() && tokens_[position_ + 1].text == ":") { consume(); require(":"); }
        while (!at("ret")) instruction();
        require("ret"); require("void"); require("}");
        if (take("attributes")) attributeDefinition();
        if (functionAttributes_ >= 0 && !attributesSeen_) fail("Missing AIR function attribute group");
        while (!at("")) metadataDefinition();
        validateMetadata();
        if (!stores_) fail("AIR kernel must store to its current thread element");
        CompileResult result;
        result.reflection.entry = entry_;
        result.reflection.threadIndexName = threadName_;
        result.reflection.buffers.push_back(BufferBinding{bufferName_, 0, "uint", true});
        result.openclSource = "// Mellow AIR 2.7 SSA subset; host must enforce exact 1D dispatch.\n__kernel void " + entry_ + "(__global uint *mellow_buffer0) {\n  const uint mellow_gid = (uint)get_global_id(0);\n" + body_ + "}\n";
        result.success = true;
        return result;
    }
private:
    std::string ssaName() {
        require("%");
        if (peek().quoted || peek().text.empty() || !(digit(peek().text[0]) || alpha(peek().text[0]) || peek().text[0] == '.')) fail("Invalid SSA name");
        return consume();
    }
    void pointerType() { require("ptr"); require("addrspace"); require("("); require("1"); require(")"); }
    void argumentDecorations() {
        take("noundef");
        if (peek().quoted) { if (quoted() != "air-buffer-no-alias") fail("Unsupported AIR parameter attribute"); }
    }
    AirValue lookup(AirType type) {
        const auto n = ssaName(); auto it = values_.find(n);
        if (it == values_.end() || it->second.type != type) fail("Undefined SSA value or type mismatch");
        return it->second;
    }
    AirValue u32() {
        if (at("%")) return lookup(AirType::U32);
        bool negative = take("-");
        auto value = decimal(negative ? uint64_t(INT32_MAX) + 1 : UINT32_MAX);
        uint32_t bits = negative ? uint32_t(0u - static_cast<uint32_t>(value)) : static_cast<uint32_t>(value);
        return AirValue{AirType::U32, std::to_string(bits) + "u", false, false};
    }
    void define(const std::string &name, AirValue value) {
        if (!values_.emplace(name, std::move(value)).second) fail("SSA value defined more than once");
    }
    void aligned() { require(","); require("align"); require("4"); }
    void instruction() {
        if (++instructions_ > MaxStatements) fail("AIR instruction budget exceeded");
        if (take("store")) {
            require("i32"); auto value = u32(); require(","); pointerType(); auto pointer = lookup(AirType::Pointer);
            if (!pointer.elementPointer) fail("AIR store does not address the exact thread element");
            aligned(); body_ += "  mellow_buffer0[mellow_gid] = " + value.emitted + ";\n"; ++stores_; return;
        }
        const auto nameValue = ssaName(); require("="); const auto op = consume();
        if (op == "extractelement") {
            require("<"); require("3"); require("x"); require("i32"); require(">"); lookup(AirType::Thread3);
            require(","); require("i64"); require("0");
            define(nameValue, AirValue{AirType::U32, "mellow_gid", true, false}); return;
        }
        if (op == "zext") {
            require("i32"); auto index = lookup(AirType::U32); require("to"); require("i64");
            if (!index.exactIndex) fail("Only thread-index zero extension is supported");
            define(nameValue, AirValue{AirType::Index64, "mellow_gid", true, false}); return;
        }
        if (op == "getelementptr") {
            take("inbounds"); require("i32"); require(","); pointerType();
            auto base = lookup(AirType::Pointer);
            if (base.elementPointer) fail("AIR nested pointer arithmetic is unsupported");
            // LLVM GEP sign-extends narrow indices. Only a proven i32->i64
            // zext is equivalent for the full unsigned dispatch contract.
            require(","); require("i64"); auto index = lookup(AirType::Index64);
            if (!index.exactIndex) fail("AIR GEP index must be the exact current thread index");
            define(nameValue, AirValue{AirType::Pointer, "mellow_buffer0 + mellow_gid", false, true}); return;
        }
        std::string expression;
        if (op == "load") {
            require("i32"); require(","); pointerType(); auto pointer = lookup(AirType::Pointer);
            if (!pointer.elementPointer) fail("AIR load does not address the exact thread element");
            aligned(); expression = "mellow_buffer0[mellow_gid]";
        } else {
            static const std::map<std::string, std::string> ops = {{"add", "+"}, {"sub", "-"}, {"mul", "*"}, {"and", "&"}, {"or", "|"}, {"xor", "^"}, {"shl", "<<"}, {"lshr", ">>"}, {"udiv", "/"}, {"urem", "%"}};
            auto it = ops.find(op); if (it == ops.end()) fail("Unsupported AIR instruction: " + op);
            require("i32"); auto a = u32(); require(",");
            if ((op == "shl" || op == "lshr" || op == "udiv" || op == "urem") && at("%")) fail("AIR shift/divisor must be a checked constant");
            auto b = u32();
            if (op == "shl" || op == "lshr" || op == "udiv" || op == "urem") {
                uint64_t constant = std::stoull(b.emitted);
                if (((op == "shl" || op == "lshr") && constant >= 32) || ((op == "udiv" || op == "urem") && constant == 0)) fail("AIR shift/divisor outside defined range");
            }
            expression = "(" + a.emitted + " " + it->second + " " + b.emitted + ")";
        }
        const std::string emitted = "mellow_ssa" + std::to_string(values_.size());
        body_ += "  const uint " + emitted + " = " + expression + ";\n";
        define(nameValue, AirValue{AirType::U32, emitted, false, false});
    }
    void attributeDefinition() {
        require("#"); auto id = decimal(UINT32_MAX);
        if (functionAttributes_ < 0 || static_cast<uint64_t>(functionAttributes_) != id) fail("Unexpected AIR attribute group");
        require("="); require("{");
        while (!take("}")) {
            if (peek().quoted) {
                auto key = quoted(); require("="); auto value = quoted();
                if (!((key == "frame-pointer" && value == "all") || (key == "no-trapping-math" && value == "true") || (key == "min-legal-vector-width" && (value == "0" || value == "96")) || (key == "stack-protector-buffer-size" && value == "8"))) fail("Unsupported AIR string attribute");
            } else {
                auto attribute = consume();
                if (attribute != "nounwind" && attribute != "mustprogress" && attribute != "willreturn" && attribute != "norecurse") fail("Unsupported AIR function attribute");
            }
        }
        attributesSeen_ = true;
    }
    Metadata metadata(size_t depth = 0) {
        if (depth > MaxExpressionDepth || ++metadataNodes_ > MaxAstNodes) fail("AIR metadata budget exceeded");
        Metadata value;
        if (take("i32")) { value.kind = Metadata::Kind::Integer; value.integer = static_cast<uint32_t>(decimal(UINT32_MAX)); return value; }
        if (take("ptr")) { require("@"); value.kind = Metadata::Kind::Function; value.text = name(); return value; }
        require("!");
        if (peek().quoted) { value.kind = Metadata::Kind::String; value.text = quoted(); return value; }
        if (take("{")) {
            value.kind = Metadata::Kind::List;
            if (!take("}")) { do { value.list.push_back(metadata(depth + 1)); } while (take(",")); require("}"); }
        } else { value.kind = Metadata::Kind::Reference; value.integer = static_cast<uint32_t>(decimal(UINT32_MAX)); }
        return value;
    }
    void metadataDefinition() {
        require("!");
        if (!peek().text.empty() && digit(peek().text[0])) {
            auto id = static_cast<uint32_t>(decimal(UINT32_MAX)); require("="); auto value = metadata();
            if (value.kind != Metadata::Kind::List || !metadata_.emplace(id, std::move(value)).second) fail("AIR metadata duplicate or non-list definition");
        } else {
            auto key = consume();
            if (key != "air.kernel" && key != "air.version" && key != "air.language_version") fail("Unsupported AIR named metadata: " + key);
            require("="); auto value = metadata();
            if (value.kind != Metadata::Kind::List || !named_.emplace(key, std::move(value)).second) fail("AIR named metadata duplicate or non-list");
        }
    }
    const std::vector<Metadata> &dereference(const Metadata &m) {
        if (m.kind != Metadata::Kind::Reference) fail("Expected AIR metadata reference");
        auto it = metadata_.find(m.integer); if (it == metadata_.end()) fail("Undefined AIR metadata reference");
        usedMetadata_.insert(m.integer); return it->second.list;
    }
    const std::vector<Metadata> &named(const std::string &nameValue) {
        auto it = named_.find(nameValue);
        if (it == named_.end() || it->second.list.size() != 1) fail("Required AIR named metadata is missing or ambiguous");
        return dereference(it->second.list[0]);
    }
    static bool integer(const Metadata &m, uint32_t value) { return m.kind == Metadata::Kind::Integer && m.integer == value; }
    static bool string(const Metadata &m, const std::string &value) { return m.kind == Metadata::Kind::String && m.text == value; }
    void validateMetadata() {
        const auto &version = named("air.version");
        if (version.size() != 3 || !integer(version[0], 2) || !integer(version[1], 7) || !integer(version[2], 0)) fail("AIR metadata version must be 2.7.0");
        const auto &language = named("air.language_version");
        if (language.size() != 4 || !string(language[0], "Metal") || !integer(language[1], 3) || !integer(language[2], 2) || !integer(language[3], 0)) fail("AIR language metadata must be Metal 3.2.0");
        const auto &kernel = named("air.kernel");
        if (kernel.size() != 3 || kernel[0].kind != Metadata::Kind::Function || kernel[0].text != entry_) fail("AIR kernel metadata/function mismatch");
        if (!dereference(kernel[1]).empty()) fail("AIR kernel output metadata must be empty");
        const auto &args = dereference(kernel[2]);
        if (args.size() != 2) fail("AIR kernel metadata must describe exactly two arguments");
        const auto &buffer = dereference(args[0]);
        if (buffer.size() != 16 || !integer(buffer[0], 0) || !string(buffer[1], "air.buffer") || !string(buffer[2], "air.location_index") || !integer(buffer[3], 0) || !integer(buffer[4], 1) || !string(buffer[5], "air.read_write") || !string(buffer[6], "air.address_space") || !integer(buffer[7], 1) || !string(buffer[8], "air.arg_type_size") || !integer(buffer[9], 4) || !string(buffer[10], "air.arg_type_align_size") || !integer(buffer[11], 4) || !string(buffer[12], "air.arg_type_name") || !string(buffer[13], "uint") || !string(buffer[14], "air.arg_name") || buffer[15].kind != Metadata::Kind::String || !identifier(buffer[15].text)) fail("AIR buffer ABI metadata mismatch");
        const auto &thread = dereference(args[1]);
        if (thread.size() != 6 || !integer(thread[0], 1) || !string(thread[1], "air.thread_position_in_grid") || !string(thread[2], "air.arg_type_name") || !string(thread[3], vectorThread_ ? "uint3" : "uint") || !string(thread[4], "air.arg_name") || thread[5].kind != Metadata::Kind::String || !identifier(thread[5].text)) fail("AIR thread-index ABI metadata mismatch");
        if (usedMetadata_.size() != metadata_.size()) fail("AIR module contains unvalidated metadata");
        bufferName_ = buffer[15].text; threadName_ = thread[5].text;
    }
    std::string entry_, bufferSsa_, threadSsa_, body_, bufferName_, threadName_;
    bool vectorThread_ = false, attributesSeen_ = false;
    int64_t functionAttributes_ = -1;
    size_t instructions_ = 0, stores_ = 0, metadataNodes_ = 0;
    std::map<std::string, AirValue> values_;
    std::map<uint32_t, Metadata> metadata_;
    std::map<std::string, Metadata> named_;
    std::set<uint32_t> usedMetadata_;
};

} // namespace

CompileResult compileMsl(const std::string &source, const std::string &entry) {
    try { return MslParser(source, entry).run(); }
    catch (const Failure &e) { CompileResult r; r.diagnostics.push_back(e.what()); return r; }
}

CompileResult compileAir(const std::vector<uint8_t> &, const std::string &) {
    CompileResult r;
    r.diagnostics.push_back("Raw AIR requires an actual LLVM bitcode decoder; pass decoded assembly to compileAirText. Magic alone is not AIR validation.");
    return r;
}

CompileResult compileAir(const std::vector<uint8_t> &bitcode, const std::string &entry,
                         const std::string &llvmLibrary) {
    std::string ir, error;
    if (!decodeAirBitcode(bitcode, llvmLibrary, ir, error)) {
        CompileResult result;
        result.diagnostics.push_back(error.empty() ? "LLVM AIR decoding failed" : error);
        return result;
    }
    return compileAirText(ir, entry);
}

CompileResult compileAirText(const std::string &ir, const std::string &entry) {
    try { return AirParser(ir, entry).run(); }
    catch (const Failure &e) { CompileResult r; r.diagnostics.push_back(e.what()); return r; }
}

} } // namespace MellowRT::ShaderJit
