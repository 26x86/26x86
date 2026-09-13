// Independently authored load, store, and instruction-fetch permission probes.
.text
.global hierarchy_load
hierarchy_load:
    ldr x2, [x0]
    hlt #0
.global hierarchy_store
hierarchy_store:
    str x1, [x0]
    hlt #0
.global hierarchy_fetch
hierarchy_fetch:
    hlt #0
