// Native Intel compiler backend evidence. OpenCL C, NOT Metal Shading Language.
// Compilation does not submit this program to any GPU.
__kernel void mellow_evidence(__global const uint *input,
                              __global uint *output,
                              const uint nonce,
                              const uint count) {
    const uint i = (uint)get_global_id(0);
    if (i < count) {
        const uint x = input[i] ^ nonce;
        output[i] = (x * 1664525u + 1013904223u) ^ (i * 2654435761u);
    }
}
