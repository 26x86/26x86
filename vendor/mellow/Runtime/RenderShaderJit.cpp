// SPDX-License-Identifier: MIT
#include "RenderShaderJit.hpp"
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <map>
#include <locale>
#include <set>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace MellowRT { namespace RenderShaderJit {
namespace {
struct Invalid : std::runtime_error { using std::runtime_error::runtime_error; };
bool alpha(char c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_'; }
bool digit(char c) { return c >= '0' && c <= '9'; }
bool identifier(const std::string &s) {
    if (s.empty() || !alpha(s[0])) return false;
    for (char c : s) if (!alpha(c) && !digit(c)) return false;
    return true;
}
bool reserved(const std::string &s) {
    static const std::set<std::string> words {
        "alignas", "alignof", "and", "and_eq", "asm", "atomic", "auto", "bitand", "bitor", "bool", "break",
        "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const",
        "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await", "co_return", "co_yield",
        "decltype", "default", "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit", "export",
        "extern", "false", "float", "float2", "float3", "float4", "for", "friend", "goto", "half", "if",
        "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
        "operator", "or", "or_eq", "private", "protected", "public", "register", "reinterpret_cast",
        "requires", "return", "short", "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
        "switch", "template", "this", "thread_local", "throw", "true", "try", "typedef", "typeid", "typename",
        "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
        "constant", "device", "thread", "threadgroup", "threadgroup_imageblock", "kernel", "vertex", "fragment",
        "object", "mesh", "tile", "uint", "uchar", "ushort", "ulong", "sampler", "texture2d", "metal"
    };
    return words.count(s) || s.find("__") != std::string::npos;
}
std::vector<std::string> lex(const std::string &s) {
    if (s.empty() || s.size() > MaxSourceBytes) throw Invalid("Source must contain 1-65536 bytes");
    std::vector<std::string> out;
    size_t p = 0;
    while (p < s.size()) {
        if (out.size() >= 8192) throw Invalid("Token limit exceeded");
        if (std::isspace(static_cast<unsigned char>(s[p]))) { ++p; continue; }
        if (s.compare(p, 2, "//") == 0) { auto e = s.find('\n', p + 2); p = e == std::string::npos ? s.size() : e; continue; }
        if (s.compare(p, 2, "/*") == 0) { auto e = s.find("*/", p + 2); if (e == std::string::npos) throw Invalid("Unterminated comment"); p = e + 2; continue; }
        size_t begin = p;
        if (alpha(s[p])) { while (p < s.size() && (alpha(s[p]) || digit(s[p]))) ++p; }
        else if (digit(s[p]) || (s[p] == '.' && p + 1 < s.size() && digit(s[p + 1]))) {
            while (p < s.size() && digit(s[p])) ++p;
            if (p < s.size() && s[p] == '.') { ++p; while (p < s.size() && digit(s[p])) ++p; }
            if (p < s.size() && (s[p] == 'e' || s[p] == 'E')) {
                ++p; if (p < s.size() && (s[p] == '+' || s[p] == '-')) ++p;
                auto exponent = p; while (p < s.size() && digit(s[p])) ++p;
                if (p == exponent) throw Invalid("Missing exponent digits");
            }
            if (p < s.size() && (s[p] == 'f' || s[p] == 'F' || s[p] == 'u')) ++p;
        } else {
            const std::string punctuation = "#<>(){}[],;=.+-*/&";
            if (punctuation.find(s[p]) == std::string::npos) throw Invalid("Unsupported character in render shader");
            ++p;
        }
        if (p - begin > 128) throw Invalid("Token length limit exceeded");
        out.push_back(s.substr(begin, p - begin));
    }
    out.push_back("");
    return out;
}
// lanes=0 is uint, lanes=1..4 are float/float vectors; arrays are separately typed.
struct Expr { unsigned lanes {}; std::string code; bool number {}; double value {}; };
struct Symbol { unsigned lanes {}, arrayCount {}; std::string code; bool vertexId {}; };
std::string type(unsigned n) { return n == 0 ? "uint" : n == 1 ? "float" : "vec" + std::to_string(n); }
unsigned parseType(const std::string &s) {
    if (s == "uint") return 0;
    if (s == "float") return 1;
    if (s == "float2") return 2;
    if (s == "float3") return 3;
    if (s == "float4") return 4;
    throw Invalid("Only uint and float/float2/float3/float4 types are admitted");
}
struct Parser {
    std::vector<std::string> tokens;
    size_t pos {}, nodes {}, statements {}, nextName {};
    std::map<std::string, Symbol> symbols;
    std::set<std::string> functions;
    Stage stage {};
    bool usesParams {}, usesPosition {}, hasVertexId {};
    std::string body;
    explicit Parser(const std::string &s) : tokens(lex(s)) {}
    const std::string &peek() const { return tokens.at(pos); }
    bool take(const std::string &s) { if (peek() == s) { ++pos; return true; } return false; }
    void need(const std::string &s) { if (!take(s)) throw Invalid("Expected '" + s + "', received '" + peek() + "'"); }
    std::string name() { auto s = peek(); if (!identifier(s)) throw Invalid("Expected identifier"); ++pos; return s; }
    std::string fresh() { return "mellow_local_" + std::to_string(nextName++); }
    void bind(const std::string &name, Symbol value) {
        if (reserved(name) || symbols.count(name)) throw Invalid("Duplicate/reserved identifier");
        symbols.emplace(name, std::move(value));
    }
    void attribute(const std::string &name, bool binding = false) {
        need("["); need("["); need(name);
        if (binding) { need("("); need("0"); need(")"); }
        need("]"); need("]");
    }
    Expr convertScalar(Expr v) {
        if (v.lanes == 0) { v.code = "float(" + v.code + ")"; v.lanes = 1; if (v.number) v.value = static_cast<float>(v.value); }
        return v;
    }
    Expr primary(size_t depth) {
        if (++nodes > 4096 || depth > 48) throw Invalid("Expression complexity limit exceeded");
        Expr e;
        if (take("(")) { e = expression(0, depth + 1); need(")"); }
        else if (take("+")) { e = primary(depth + 1); if (!e.lanes) throw Invalid("Unary plus requires float"); }
        else if (take("-")) {
            e = primary(depth + 1); if (!e.lanes) throw Invalid("Use a float literal for a negative value");
            e.code = "(-" + e.code + ")"; if (e.number) e.value = -e.value;
        } else if (!peek().empty() && (digit(peek()[0]) || peek()[0] == '.')) {
            auto text = tokens[pos++]; bool fl = text.find_first_of(".eEfF") != std::string::npos;
            if (fl && text.back() == 'u') throw Invalid("A float literal cannot carry a uint suffix");
            if ((text.back() == 'f' || text.back() == 'F') && text.find_first_of(".eE") == std::string::npos)
                throw Invalid("A float literal needs a decimal point or exponent before its suffix");
            if (text.back() == 'f' || text.back() == 'F' || text.back() == 'u') text.pop_back();
            if (!fl && text.size() > 1 && text[0] == '0') throw Invalid("Octal integer literals are not admitted");
            std::istringstream input(text); input.imbue(std::locale::classic()); double value = 0.0; input >> value;
            if (!input || input.peek() != std::char_traits<char>::eof() || !std::isfinite(value) || value > (fl ? 1.e30 : 4294967295.0)) throw Invalid("Literal out of admitted range");
            if (fl) value = static_cast<float>(value);
            if (!fl && std::floor(value) != value) throw Invalid("Invalid uint literal");
            e = {fl ? 1u : 0u, fl ? (text.find_first_of(".eE") == std::string::npos ? text + ".0" : text) : text + "u", true, value};
        } else {
            auto id = name();
            if (id == "float" || id == "float2" || id == "float3" || id == "float4") {
                const unsigned lanes = parseType(id); need("(");
                std::vector<Expr> args;
                do { args.push_back(convertScalar(expression(0, depth + 1))); if (args.size() > 4) throw Invalid("Constructor argument limit"); } while (take(","));
                need(")"); unsigned count = 0; for (auto &a : args) count += a.lanes;
                if (!(args.size() == 1 && args[0].lanes == 1) && count != lanes) throw Invalid("Constructor component count mismatch");
                if (lanes == 1 && count != 1) throw Invalid("Vector-to-scalar truncation is not admitted");
                e.lanes = lanes; e.code = type(lanes) + "(";
                for (size_t i = 0; i < args.size(); ++i) e.code += (i ? ", " : "") + args[i].code;
                e.code += ")"; e.number = lanes == 1 && args.size() == 1 && args[0].number;
                if (e.number) e.value = args[0].value;
            } else {
                auto it = symbols.find(id); if (it == symbols.end()) throw Invalid("Unknown variable/function '" + id + "'");
                auto sym = it->second; e = {sym.lanes, sym.code, false, 0.0};
                if (sym.arrayCount) {
                    need("["); auto indexName = name(); auto index = symbols.find(indexName);
                    if (index == symbols.end() || !index->second.vertexId || stage != Stage::Vertex) throw Invalid("Array index must be the exact vertex_id parameter");
                    need("]"); e.code += "[int(" + index->second.code + ")]";
                }
            }
        }
        while (take(".")) {
            auto fields = name(); if (e.lanes < 2 || fields.size() > 4) throw Invalid("Invalid vector swizzle");
            int family = -1;
            for (char c : fields) {
                auto xy = std::string("xyzw").find(c), rgba = std::string("rgba").find(c);
                int group = xy != std::string::npos ? 0 : 1; auto index = group == 0 ? xy : rgba;
                if (index >= e.lanes || (family != -1 && family != group)) throw Invalid("Out-of-range/mixed swizzle");
                family = group;
            }
            e.code = "(" + e.code + ")." + fields; e.lanes = static_cast<unsigned>(fields.size()); e.number = false;
        }
        return e;
    }
    Expr expression(int minPrecedence = 0, size_t depth = 0) {
        auto lhs = primary(depth + 1);
        while (true) {
            auto op = peek(); int precedence = op == "+" || op == "-" ? 1 : op == "*" || op == "/" ? 2 : -1;
            if (precedence < minPrecedence) break;
            ++pos; auto rhs = expression(precedence + 1, depth + 1);
            if (!lhs.lanes || !rhs.lanes) throw Invalid("Arithmetic requires explicit float operands");
            if (lhs.lanes != rhs.lanes && lhs.lanes != 1 && rhs.lanes != 1) throw Invalid("Vector width mismatch");
            if (op == "/" && (!rhs.number || rhs.lanes != 1 || rhs.value == 0.0)) throw Invalid("Division needs a nonzero constant scalar");
            bool number = lhs.number && rhs.number;
            double value = 0.0;
            if (number) {
                value = op == "+" ? lhs.value + rhs.value : op == "-" ? lhs.value - rhs.value : op == "*" ? lhs.value * rhs.value : lhs.value / rhs.value;
                value = static_cast<float>(value);
                if (!std::isfinite(value) || std::abs(value) > 1.e30) throw Invalid("Constant expression out of range");
            }
            lhs = {lhs.lanes > rhs.lanes ? lhs.lanes : rhs.lanes, "(" + lhs.code + " " + op + " " + rhs.code + ")", number, value};
        }
        return lhs;
    }
    CompileResult function() {
        symbols.clear(); body.clear(); usesParams = usesPosition = hasVertexId = false;
        if (take("vertex")) stage = Stage::Vertex;
        else if (take("fragment")) stage = Stage::Fragment;
        else throw Invalid("Only vertex/fragment entry functions are admitted");
        need("float4"); auto entry = name();
        if (reserved(entry)) throw Invalid("Entry name is a reserved keyword");
        if (!functions.insert(entry).second || functions.size() > 8) throw Invalid("Duplicate entry or too many functions");
        need("(");
        if (!take(")")) {
            do {
                if (take("constant")) {
                    need("float4"); need("&"); auto id = name(); attribute("buffer", true);
                    if (usesParams) throw Invalid("Only one float4 parameter binding is admitted");
                    usesParams = true; bind(id, {4, 0, "mellow_params", false});
                } else if (take("uint")) {
                    auto id = name(); attribute("vertex_id");
                    if (stage != Stage::Vertex || hasVertexId) throw Invalid("vertex_id stage/duplicate mismatch");
                    hasVertexId = true; bind(id, {0, 0, "uint(gl_VertexID)", true});
                } else if (take("float4")) {
                    auto id = name(); attribute("position");
                    if (stage != Stage::Fragment || usesPosition) throw Invalid("position stage/duplicate mismatch");
                    usesPosition = true; bind(id, {4, 0, "vec4(gl_FragCoord.x, mellow_viewport.y - gl_FragCoord.y, gl_FragCoord.zw)", false});
                } else throw Invalid("Unsupported entry parameter");
            } while (take(","));
            need(")");
        }
        if (peek() == "[") { if (stage != Stage::Fragment) throw Invalid("float4 vertex return must not have an attribute"); attribute("color", true); }
        need("{"); bool returned = false;
        while (!take("}")) {
            if (++statements > 256) throw Invalid("Statement limit exceeded");
            if (take("return")) {
                auto value = expression(); if (value.lanes != 4) throw Invalid("Entry must return float4"); need(";");
                body += "  vec4 mellow_value = " + value.code + ";\n";
                if (stage == Stage::Vertex) body += "  gl_Position = vec4(mellow_value.xy, 2.0 * mellow_value.z - mellow_value.w, mellow_value.w);\n";
                else body += "  mellow_color = mellow_value;\n";
                returned = true; need("}"); break;
            }
            bool constant = take("const"); auto lanes = parseType(name());
            if (!lanes) throw Invalid("Local uint values are not admitted");
            auto id = name(); auto glname = fresh();
            if (take("[")) {
                if (stage != Stage::Vertex || !constant || !hasVertexId) throw Invalid("Arrays require const vertex values and vertex_id");
                need("3"); need("]"); need("="); need("{");
                std::string init;
                for (int i = 0; i < 3; ++i) {
                    if (i) need(",");
                    auto val = expression();
                    if (val.lanes != lanes) throw Invalid("Array initializer type mismatch");
                    init += (i ? ", " : "") + val.code;
                }
                need("}"); need(";"); bind(id, {lanes, 3, glname, false});
                body += "  " + type(lanes) + " " + glname + "[3] = " + type(lanes) + "[3](" + init + ");\n";
            } else {
                need("="); auto value = expression(); need(";");
                if (value.lanes != lanes) throw Invalid("Local initializer type mismatch");
                bind(id, {lanes, 0, glname, false}); body += "  " + type(lanes) + " " + glname + " = " + value.code + ";\n";
            }
        }
        if (!returned) throw Invalid("Entry needs one final return statement");
        CompileResult result;
        result.success = true; result.stage = stage; result.entry = entry;
        result.usesParameters = usesParams; result.usesFragmentPosition = usesPosition;
        result.glslSource = "#version 330 core\n";
        if (usesParams) result.glslSource += "uniform vec4 mellow_params;\n";
        if (usesPosition) result.glslSource += "uniform vec2 mellow_viewport;\n";
        if (stage == Stage::Fragment) result.glslSource += "layout(location=0) out vec4 mellow_color;\n";
        result.glslSource += "void main() {\n" + body + "}\n";
        return result;
    }
    CompileResult run(const std::string &entry, Stage requested) {
        if (!identifier(entry) || reserved(entry) || entry.size() > 128) throw Invalid("Invalid requested entry name");
        if (take("#")) { need("include"); need("<"); need("metal_stdlib"); need(">"); }
        if (take("using")) { need("namespace"); need("metal"); need(";"); }
        CompileResult selected; bool found = false;
        while (!peek().empty()) {
            auto compiled = function();
            if (compiled.entry == entry) {
                if (compiled.stage != requested) throw Invalid("Requested entry stage mismatch");
                selected = std::move(compiled); found = true;
            }
        }
        if (!found) throw Invalid("Requested entry not found");
        return selected;
    }
};
}
CompileResult compileMsl(const std::string &source, const std::string &entry, Stage stage) {
    try { return Parser(source).run(entry, stage); }
    catch (const Invalid &error) { CompileResult r; r.stage = stage; r.entry = entry; r.diagnostics.push_back(error.what()); return r; }
}
} }
