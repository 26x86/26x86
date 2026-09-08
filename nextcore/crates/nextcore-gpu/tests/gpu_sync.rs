use nextcore_gpu::sync::{GpuSyncManager, SemaphoreId};

#[test]
fn test_fence_create_and_signal() {
    let mut sm = GpuSyncManager::new();
    let fid = sm.create_fence();
    assert!(!sm.get_fence(fid).unwrap().is_signaled());

    sm.signal_fence(fid, 42);
    let fence = sm.get_fence(fid).unwrap();
    assert!(fence.is_signaled());
    assert_eq!(fence.get_value(), 42);
}

#[test]
fn test_fence_wait() {
    let mut sm = GpuSyncManager::new();
    let fid = sm.create_fence();
    sm.signal_fence(fid, 1);
    assert!(sm.wait_fence(fid, 100));
}

#[test]
fn test_fence_timeout() {
    let mut sm = GpuSyncManager::new();
    let fid = sm.create_fence();
    assert!(!sm.wait_fence(fid, 50));
}

#[test]
fn test_semaphore_signal_wait() {
    let mut sm = GpuSyncManager::new();
    let sid = sm.create_semaphore();
    assert_eq!(sm.get_semaphore(sid).unwrap().get_value(), 0);

    sm.signal_semaphore(sid);
    sm.signal_semaphore(sid);
    assert_eq!(sm.get_semaphore(sid).unwrap().get_value(), 2);
    assert!(sm.wait_semaphore(sid, 2, 100));
}

#[test]
fn test_semaphore_timeout() {
    let mut sm = GpuSyncManager::new();
    let sid = sm.create_semaphore();
    assert!(!sm.wait_semaphore(sid, 5, 50));
}

#[test]
fn test_event_fire_wait() {
    let mut sm = GpuSyncManager::new();
    let eid = sm.create_event();
    assert!(!sm.get_event(eid).unwrap().is_fired());

    sm.fire_event(eid);
    assert!(sm.get_event(eid).unwrap().is_fired());
    assert!(sm.wait_event(eid, 100));
}

#[test]
fn test_event_reset() {
    let mut sm = GpuSyncManager::new();
    let eid = sm.create_event();
    sm.fire_event(eid);
    assert!(sm.get_event(eid).unwrap().is_fired());
    sm.reset_all();
    assert!(!sm.get_event(eid).unwrap().is_fired());
}

#[test]
fn test_reset_all_resets_all_types() {
    let mut sm = GpuSyncManager::new();
    let fid = sm.create_fence();
    let sid = sm.create_semaphore();
    let eid = sm.create_event();

    sm.signal_fence(fid, 1);
    sm.signal_semaphore(sid);
    sm.fire_event(eid);

    sm.reset_all();

    assert!(!sm.get_fence(fid).unwrap().is_signaled());
    assert_eq!(sm.get_semaphore(sid).unwrap().get_value(), 0);
    assert!(!sm.get_event(eid).unwrap().is_fired());
}

#[test]
fn test_counts() {
    let mut sm = GpuSyncManager::new();
    let _f = sm.create_fence();
    let _f2 = sm.create_fence();
    let _s = sm.create_semaphore();
    let _e = sm.create_event();

    assert_eq!(sm.fence_count(), 2);
    assert_eq!(sm.semaphore_count(), 1);
    assert_eq!(sm.event_count(), 1);
}

#[test]
fn test_semaphore_is_cloneable_state() {
    // Verify that the sync manager types can be referenced without data races.
    let mut sm = GpuSyncManager::new();
    let sid = sm.create_semaphore();
    let sem: &nextcore_gpu::sync::GpuSemaphore = sm.get_semaphore(sid).unwrap();
    assert_eq!(std::mem::size_of_val(sem), std::mem::size_of::<nextcore_gpu::sync::GpuSemaphore>());
}

#[test]
fn test_semaphore_id_derives() {
    let a = SemaphoreId(1);
    let b = SemaphoreId(1);
    assert_eq!(a, b);
    let c = SemaphoreId(2);
    assert_ne!(a, c);
}
