//! QARMA5 and the bounded AArch64 v8.3 pointer-authentication policy.
//! Independently expressed nibble-array implementation of the public cipher.
//! No allocation, host crypto library, vendor firmware or hardware dependency.

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
#[repr(C)]
pub(crate) struct Key {
    pub(crate) lo: u64,
    pub(crate) hi: u64,
}

const SUB: [u8; 16] = [11, 6, 8, 15, 12, 0, 9, 14, 3, 7, 4, 5, 13, 2, 1, 10];
const SHUFFLE: [usize; 16] = [13, 6, 11, 0, 7, 12, 1, 10, 8, 3, 14, 5, 2, 9, 4, 15];
const TWEAK: [usize; 16] = [4, 5, 6, 7, 11, 2, 3, 8, 12, 13, 14, 15, 0, 1, 10, 9];
const TWEAK_LFSR: [usize; 7] = [2, 4, 7, 11, 12, 14, 15];
const ROUND: [u64; 5] = [0, 0x13198a2e03707344, 0xa4093822299f31d0,
    0x082efa98ec4e6c89, 0x452821e638d01377];
const ALPHA: u64 = 0xc0ac29b7c97c50dd;

type Cells = [u8; 16];

fn cells(word: u64) -> Cells {
    core::array::from_fn(|index| ((word >> (index * 4)) & 15) as u8)
}

fn packed(value: Cells) -> u64 {
    value.iter().enumerate().fold(0, |word, (i, cell)| word | (u64::from(*cell) << (i * 4)))
}

fn xor(state: &mut Cells, word: u64) {
    for (i, cell) in state.iter_mut().enumerate() {
        *cell ^= ((word >> (i * 4)) & 15) as u8;
    }
}

fn permutation(value: Cells, map: &[usize; 16], inverse: bool) -> Cells {
    let mut result = [0; 16];
    for i in 0..16 {
        if inverse { result[map[i]] = value[i]; }
        else { result[i] = value[map[i]]; }
    }
    result
}

fn substitute(value: &mut Cells, inverse: bool) {
    for cell in value {
        *cell = if inverse {
            // The inverse table is generated from the one public bijection.
            SUB.iter().position(|x| x == cell).unwrap_or(0) as u8
        } else { SUB[*cell as usize] };
    }
}

fn mix(value: Cells) -> Cells {
    const ROTATION: [[u8; 4]; 4] = [[0,1,2,1], [1,0,1,2], [2,1,0,1], [1,2,1,0]];
    let mut output = [0; 16];
    for column in 0..4 {
        for row in 0..4 {
            for source in 0..4 {
                let amount = ROTATION[row][source];
                if amount != 0 {
                    let cell = value[column + 4 * source];
                    output[column + 4 * row] ^= ((cell << amount) | (cell >> (4 - amount))) & 15;
                }
            }
        }
    }
    output
}

fn tweak(value: Cells, inverse: bool) -> Cells {
    let mut result = if inverse { value } else { permutation(value, &TWEAK, false) };
    for index in TWEAK_LFSR {
        let cell = result[index];
        result[index] = if inverse {
            ((cell << 1) & 15) | ((cell ^ (cell >> 3)) & 1)
        } else { (cell >> 1) | (((cell ^ (cell >> 1)) & 1) << 3) };
    }
    if inverse { permutation(result, &TWEAK, true) } else { result }
}

pub(crate) fn qarma5(data: u64, modifier: u64, key: Key) -> u64 {
    let whitening = key.hi.rotate_right(1) ^ (key.hi >> 63);
    let mut state = cells(data ^ key.hi);
    let mut schedule = cells(modifier);
    for (round, constant) in ROUND.iter().enumerate() {
        xor(&mut state, key.lo ^ packed(schedule) ^ constant);
        if round != 0 { state = mix(permutation(state, &SHUFFLE, false)); }
        substitute(&mut state, false);
        schedule = tweak(schedule, false);
    }
    xor(&mut state, whitening ^ packed(schedule));
    state = mix(permutation(state, &SHUFFLE, false));
    substitute(&mut state, false);
    state = mix(permutation(state, &SHUFFLE, false));
    xor(&mut state, key.lo);
    state = permutation(state, &SHUFFLE, true);
    substitute(&mut state, true);
    state = permutation(mix(state), &SHUFFLE, true);
    xor(&mut state, key.hi ^ packed(schedule));
    for round in (0..5).rev() {
        substitute(&mut state, true);
        if round != 0 { state = permutation(mix(state), &SHUFFLE, true); }
        schedule = tweak(schedule, true);
        xor(&mut state, key.lo ^ packed(schedule) ^ ROUND[round] ^ ALPHA);
    }
    packed(state) ^ whitening
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PauthError { Unsupported }

/// Key order is instruction A/B, data A/B, generic A. Key registers reset zero.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(crate) struct PauthState { pub(crate) keys: [Key; 5] }

fn address_mask(pointer: u64, tcr: u64) -> Result<u64, PauthError> {
    let shift = if pointer & (1 << 55) != 0 { 16 } else { 0 };
    let tsz = (tcr >> shift) & 63;
    if !matches!(tsz, 16 | 17) || tcr & ((1 << 37) | (1 << 38) | (1 << 59)) != 0 {
        return Err(PauthError::Unsupported);
    }
    Ok((1u64 << (64 - tsz)) - 1)
}
fn canonical(pointer: u64, mask: u64) -> u64 {
    (pointer & mask) | if pointer & (1 << 55) != 0 { !mask } else { 0 }
}

impl PauthState {
    pub(crate) const fn reset() -> Self { Self { keys: [Key { lo: 0, hi: 0 }; 5] } }

    pub(crate) fn sign(&self, pointer: u64, modifier: u64, key: usize, tcr: u64)
        -> Result<u64, PauthError> {
        if key >= 4 { return Err(PauthError::Unsupported); }
        let mask = address_mask(pointer, tcr)?;
        // PAC selects the canonical extension from original bit 63; bit 55
        // remains the address-range selector in the returned signed pointer.
        let high = if pointer >> 63 != 0 { !mask } else { 0 };
        let original = (pointer & mask) | high;
        let mut tag = qarma5(original, modifier, self.keys[key]);
        let extension = pointer & !mask;
        if extension != 0 && extension != !mask { tag ^= 1 << 62; }
        Ok((pointer & mask) | (high & (1 << 55)) | (tag & !mask & !(1 << 55)))
    }

    pub(crate) fn authenticate(&self, pointer: u64, modifier: u64, key: usize, tcr: u64)
        -> Result<u64, PauthError> {
        if key >= 4 { return Err(PauthError::Unsupported); }
        let mask = address_mask(pointer, tcr)?;
        let original = canonical(pointer, mask);
        let expected = qarma5(original, modifier, self.keys[key]);
        if (expected ^ pointer) & !mask & !(1 << 55) == 0 { return Ok(original); }
        // FEAT_PAuth (APA=1) poisons bits 62:61, distinguishing A and B keys.
        let failure = if key & 1 == 0 { 1 } else { 2 };
        Ok((original & !(3 << 61)) | (failure << 61))
    }

    pub(crate) fn strip(pointer: u64, tcr: u64) -> Result<u64, PauthError> {
        let mask = address_mask(pointer, tcr)?;
        Ok(canonical(pointer, mask))
    }
}

/// Stable architecture-only slow-path state shared with the C JIT dispatcher.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct PauthContext {
    pub x: [u64; 31],
    pub sp: u64,
    pub pc: u64,
    pub sctlr: u64,
    pub tcr: u64,
    keys: [Key; 5],
    pub current_el: u32,
    reserved: u32,
}

const _: [(); 368] = [(); core::mem::size_of::<PauthContext>()];

impl PauthContext {
    pub(crate) fn new(x: [u64; 31], sp: u64, pc: u64, sctlr: u64, tcr: u64,
        state: PauthState, current_el: u32) -> Self {
        Self { x, sp, pc, sctlr, tcr, keys: state.keys, current_el, reserved: 0 }
    }
    pub(crate) fn state(&self) -> PauthState { PauthState { keys: self.keys } }
    fn reg(&self, index: u32, allow_sp: bool) -> u64 {
        if index < 31 { self.x[index as usize] } else if allow_sp { self.sp } else { 0 }
    }
    fn put(&mut self, index: u32, value: u64) { if index < 31 { self.x[index as usize] = value; } }
}

/// None means a different decoder owns this instruction. Err preserves state.
pub(crate) fn step(context: &mut PauthContext, word: u32) -> Option<Result<(), PauthError>> {
    let mut next = *context;
    let rd = word & 31;
    let rn = (word >> 5) & 31;
    let operation; // 0 sign, 1 authenticate, 2 strip.
    let mut key = ((word >> 10) & 3) as usize;
    let mut destination = rd;
    let pointer;
    let modifier;
    let mut branch = false;
    let mut link = false;

    // PACGA is a generic MAC; address-PAC enable bits and address size do not gate it.
    if word & 0xffe0fc00 == 0x9ac03000 {
        if context.current_el != 1 || context.reserved != 0 { return Some(Err(PauthError::Unsupported)); }
        let value = qarma5(context.reg(rn, false), context.reg((word >> 16) & 31, true),
            context.keys[4]) & 0xffff_ffff_0000_0000;
        next.put(rd, value);
        next.pc = context.pc.wrapping_add(4);
        *context = next;
        return Some(Ok(()));
    }

    // All ten key words have architected MRS/MSR encodings, never guest pointers.
    let syskey = (word >> 5) & 0x7fff;
    let key_slot = match syskey {
        0x4108..=0x410b => Some(((syskey - 0x4108) / 2, (syskey - 0x4108) & 1)),
        0x4110..=0x4113 => Some((2 + (syskey - 0x4110) / 2, (syskey - 0x4110) & 1)),
        0x4118..=0x4119 => Some((4, syskey & 1)),
        _ => None,
    };
    let mrs = word & 0xffe00000 == 0xd5200000;
    let msr = word & 0xffe00000 == 0xd5000000;
    if (mrs || msr) && (key_slot.is_some() || matches!(syskey, 0x4080 | 0x4102 | 0x4031)) {
        if context.current_el != 1 || context.reserved != 0 { return Some(Err(PauthError::Unsupported)); }
        if let Some((index, half)) = key_slot {
            if mrs {
                let key = context.keys[index as usize];
                next.put(rd, if half == 0 { key.lo } else { key.hi });
            } else {
                let value = context.reg(rd, false);
                let key = &mut next.keys[index as usize];
                if half == 0 { key.lo = value; } else { key.hi = value; }
            }
        } else if mrs {
            next.put(rd, match syskey {0x4080 => context.sctlr, 0x4102 => context.tcr, _ => 0x10});
        } else if syskey == 0x4031 { return Some(Err(PauthError::Unsupported)); }
        else if syskey == 0x4080 {
            let value = context.reg(rd, false);
            // The C JIT fallback has no MMU yet. Keep enabling it explicit.
            if value & 1 != 0 { return Some(Err(PauthError::Unsupported)); }
            next.sctlr = value;
        } else { next.tcr = context.reg(rd, false); }
        next.pc = context.pc.wrapping_add(4);
        *context = next;
        return Some(Ok(()));
    }

    if word & 0xffffc000 == 0xdac10000 {
        let zero = word & (1 << 13) != 0;
        if zero && rn != 31 { return Some(Err(PauthError::Unsupported)); }
        operation = (word >> 12) & 1;
        pointer = context.reg(rd, false);
        modifier = if zero { 0 } else { context.reg(rn, true) };
    } else if word & 0xfffffbff == (0xdac143e0 | rd) {
        operation = 2; key = 0;
        pointer = context.reg(rd, false); modifier = 0;
    } else if word == 0xd50320ff {
        operation = 2; key = 0; destination = 30;
        pointer = context.x[30]; modifier = 0;
    } else if word & 0xffffff1f == 0xd503231f {
        key = ((word >> 6) & 1) as usize;
        operation = (word >> 7) & 1; destination = 30;
        pointer = context.x[30];
        modifier = if word & 0x20 != 0 { context.sp } else { 0 };
    } else if word & 0xffffff3f == 0xd503211f {
        key = ((word >> 6) & 1) as usize;
        operation = (word >> 7) & 1; destination = 17;
        pointer = context.x[17]; modifier = context.x[16];
    } else if word & 0xffdff800 == 0xd71f0800 {
        key = ((word >> 10) & 1) as usize;
        operation = 1; branch = true; link = word & (1 << 21) != 0;
        pointer = context.reg(rn, false); modifier = context.reg(rd, true);
    } else if word & 0xffdff81f == 0xd61f081f {
        key = ((word >> 10) & 1) as usize;
        operation = 1; branch = true; link = word & (1 << 21) != 0;
        pointer = context.reg(rn, false); modifier = 0;
    } else if word == 0xd65f0bff || word == 0xd65f0fff {
        key = ((word >> 10) & 1) as usize;
        operation = 1; branch = true;
        pointer = context.x[30]; modifier = context.sp;
    } else { return None; }

    if context.current_el != 1 || context.reserved != 0 { return Some(Err(PauthError::Unsupported)); }
    let enable_bit = [31, 30, 27, 13][key];
    let state = context.state();
    let result = if operation == 2 { PauthState::strip(pointer, context.tcr) }
    else if context.sctlr & (1 << enable_bit) == 0 { Ok(pointer) }
    else if operation == 0 { state.sign(pointer, modifier, key, context.tcr) }
    else { state.authenticate(pointer, modifier, key, context.tcr) };
    let value = match result { Ok(value) => value, Err(error) => return Some(Err(error)) };
    if branch {
        if link { next.x[30] = context.pc.wrapping_add(4); }
        next.pc = value;
    } else {
        next.put(destination, value);
        next.pc = context.pc.wrapping_add(4);
    }
    *context = next;
    Some(Ok(()))
}

/// C JIT slow-path callback. Caller supplies a valid writable architecture-only
/// context; failure preserves all fields. It cannot access guest or host RAM.
#[no_mangle]
pub unsafe extern "C" fn vf_preos_pauth_step(context: *mut PauthContext, word: u32) -> i32 {
    if context.is_null() || (context as usize) & 7 != 0 { return 1; }
    match step(unsafe { &mut *context }, word) { Some(Ok(())) => 0, _ => 1 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn layer_inverses_and_involutory_matrix() {
        for word in [0, 1, u64::MAX, 0x123456789abcdef0, 0xfedcba9876543210] {
            let original = cells(word);
            assert_eq!(packed(original), word);
            assert_eq!(permutation(permutation(original, &SHUFFLE, false), &SHUFFLE, true), original);
            assert_eq!(tweak(tweak(original, false), true), original);
            assert_eq!(mix(mix(original)), original);
            let mut altered = original;
            substitute(&mut altered, false); substitute(&mut altered, true);
            assert_eq!(altered, original);
        }
    }

    #[test]
    fn qemu_executed_pacia_vector() {
        let mut state = PauthState::reset();
        state.keys[0] = Key { lo: 0x48ad369c24681357, hi: 0xb752c963db97eca8 };
        // Actual QEMU 8.2 QARMA5, 48-bit pointer, 2026-09-08 authored program.
        assert_eq!(state.sign(0x130, 0x9876, 0, 16).unwrap(), 0xbf36000000000130);
        assert_eq!(state.authenticate(0xbf36000000000130, 0x9876, 0, 16).unwrap(), 0x130);
    }

    #[test]
    fn qemu_executed_generic_mac_vectors() {
        // Top 32 bits observed from real PACGA execution on QEMU 8.2.2.
        // This validates the primitive independently of pointer formatting.
        let vectors = [
            (0,0,0,0,0x76243b95),
            (u64::MAX,u64::MAX,u64::MAX,u64::MAX,0x56b6776d),
            (0xfb623599da6e8127,0x477d469dec0b8762,0xec2802d4e0a488e9,0x84be85ce9804e94b,0xc003b939),
            (0x130,0x9876,0x48ad369c24681357,0xb752c963db97eca8,0xbf3684bf),
            (0x0123456789abcdef,0xfedcba9876543210,0x1111111111111111,0x8888888888888888,0x07277012),
            (0x8000000000000000,1,2,4,0xb31a56a5),
            (0x0123456789abcdef,0x1020304050607080,0x1122334455667788,0x8877665544332211,0x7b4ef811),
            (0xaaaaaaaaaaaaaaaa,0x5555555555555555,0,u64::MAX,0x580ee305),
        ];
        for (data, modifier, lo, hi, expected) in vectors {
            assert_eq!(qarma5(data, modifier, Key {lo, hi}) >> 32, expected);
        }
    }

    #[test]
    fn authentication_failure_and_unsupported_modes() {
        let mut state = PauthState::reset();
        let tcr = 16 | (16 << 16);
        for key in 0..4 {
            state.keys[key] = Key {lo: key as u64 + 1, hi: 0xdeadbeef};
            for pointer in [0x12345678, 0xffff800012345678] {
                let signed = state.sign(pointer, 99, key, tcr).unwrap();
                assert_eq!(state.authenticate(signed, 99, key, tcr).unwrap(), pointer);
                let corrupt = state.authenticate(signed ^ (1 << 48), 99, key, tcr).unwrap();
                assert_ne!(corrupt, pointer);
                assert_eq!((corrupt >> 61) & 3, if key & 1 == 0 { 1 } else { 2 });
                assert_eq!(PauthState::strip(signed, tcr).unwrap(), pointer);
            }
        }
        assert_eq!(state.sign(1, 2, 0, 18), Err(PauthError::Unsupported));
        assert_eq!(state.sign(1, 2, 0, tcr | (1 << 37)), Err(PauthError::Unsupported));
    }
}
