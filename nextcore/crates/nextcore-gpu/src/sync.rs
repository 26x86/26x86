use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct FenceId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct SemaphoreId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct EventId(pub u64);

#[derive(Debug)]
pub struct GpuFence {
    pub id: FenceId,
    signaled: Arc<AtomicBool>,
    value: Arc<AtomicU64>,
}

impl GpuFence {
    pub fn new(id: FenceId) -> Self {
        Self {
            id,
            signaled: Arc::new(AtomicBool::new(false)),
            value: Arc::new(AtomicU64::new(0)),
        }
    }

    pub fn is_signaled(&self) -> bool {
        self.signaled.load(Ordering::Acquire)
    }

    pub fn signal(&self, value: u64) {
        self.value.store(value, Ordering::Release);
        self.signaled.store(true, Ordering::Release);
    }

    pub fn get_value(&self) -> u64 {
        self.value.load(Ordering::Acquire)
    }

    pub fn reset(&self) {
        self.signaled.store(false, Ordering::Release);
        self.value.store(0, Ordering::Release);
    }

    pub fn clone_state(&self) -> Self {
        Self {
            id: self.id,
            signaled: Arc::clone(&self.signaled),
            value: Arc::clone(&self.value),
        }
    }
}

#[derive(Debug)]
pub struct GpuSemaphore {
    pub id: SemaphoreId,
    counter: Arc<AtomicU64>,
}

impl GpuSemaphore {
    pub fn new(id: SemaphoreId) -> Self {
        Self {
            id,
            counter: Arc::new(AtomicU64::new(0)),
        }
    }

    pub fn signal(&self) {
        self.counter.fetch_add(1, Ordering::Release);
    }

    pub fn get_value(&self) -> u64 {
        self.counter.load(Ordering::Acquire)
    }

    pub fn wait_value(&self, target: u64) -> bool {
        self.counter.load(Ordering::Acquire) >= target
    }

    pub fn reset(&self) {
        self.counter.store(0, Ordering::Release);
    }
}

#[derive(Debug)]
pub struct GpuEvent {
    pub id: EventId,
    fired: Arc<AtomicBool>,
}

impl GpuEvent {
    pub fn new(id: EventId) -> Self {
        Self {
            id,
            fired: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn fire(&self) {
        self.fired.store(true, Ordering::Release);
    }

    pub fn is_fired(&self) -> bool {
        self.fired.load(Ordering::Acquire)
    }

    pub fn reset(&self) {
        self.fired.store(false, Ordering::Release);
    }
}

pub struct GpuSyncManager {
    next_fence_id: u64,
    next_semaphore_id: u64,
    next_event_id: u64,
    fences: HashMap<u64, GpuFence>,
    semaphores: HashMap<u64, GpuSemaphore>,
    events: HashMap<u64, GpuEvent>,
}

impl Default for GpuSyncManager {
    fn default() -> Self {
        Self::new()
    }
}

impl GpuSyncManager {
    pub fn new() -> Self {
        Self {
            next_fence_id: 1,
            next_semaphore_id: 1,
            next_event_id: 1,
            fences: HashMap::new(),
            semaphores: HashMap::new(),
            events: HashMap::new(),
        }
    }

    pub fn create_fence(&mut self) -> FenceId {
        let id = FenceId(self.next_fence_id);
        self.next_fence_id += 1;
        self.fences.insert(id.0, GpuFence::new(id));
        id
    }

    pub fn get_fence(&self, id: FenceId) -> Option<&GpuFence> {
        self.fences.get(&id.0)
    }

    pub fn signal_fence(&self, id: FenceId, value: u64) {
        if let Some(fence) = self.fences.get(&id.0) {
            fence.signal(value);
        }
    }

    pub fn wait_fence(&self, id: FenceId, timeout_ms: u64) -> bool {
        if let Some(fence) = self.fences.get(&id.0) {
            let start = std::time::Instant::now();
            let timeout = std::time::Duration::from_millis(timeout_ms);
            loop {
                if fence.is_signaled() {
                    return true;
                }
                if start.elapsed() >= timeout {
                    return false;
                }
                std::thread::yield_now();
            }
        } else {
            false
        }
    }

    pub fn create_semaphore(&mut self) -> SemaphoreId {
        let id = SemaphoreId(self.next_semaphore_id);
        self.next_semaphore_id += 1;
        self.semaphores.insert(id.0, GpuSemaphore::new(id));
        id
    }

    pub fn get_semaphore(&self, id: SemaphoreId) -> Option<&GpuSemaphore> {
        self.semaphores.get(&id.0)
    }

    pub fn signal_semaphore(&self, id: SemaphoreId) {
        if let Some(sem) = self.semaphores.get(&id.0) {
            sem.signal();
        }
    }

    pub fn wait_semaphore(&self, id: SemaphoreId, target: u64, timeout_ms: u64) -> bool {
        if let Some(sem) = self.semaphores.get(&id.0) {
            let start = std::time::Instant::now();
            let timeout = std::time::Duration::from_millis(timeout_ms);
            loop {
                if sem.wait_value(target) {
                    return true;
                }
                if start.elapsed() >= timeout {
                    return false;
                }
                std::thread::yield_now();
            }
        } else {
            false
        }
    }

    pub fn create_event(&mut self) -> EventId {
        let id = EventId(self.next_event_id);
        self.next_event_id += 1;
        self.events.insert(id.0, GpuEvent::new(id));
        id
    }

    pub fn get_event(&self, id: EventId) -> Option<&GpuEvent> {
        self.events.get(&id.0)
    }

    pub fn fire_event(&self, id: EventId) {
        if let Some(event) = self.events.get(&id.0) {
            event.fire();
        }
    }

    pub fn wait_event(&self, id: EventId, timeout_ms: u64) -> bool {
        if let Some(event) = self.events.get(&id.0) {
            let start = std::time::Instant::now();
            let timeout = std::time::Duration::from_millis(timeout_ms);
            loop {
                if event.is_fired() {
                    return true;
                }
                if start.elapsed() >= timeout {
                    return false;
                }
                std::thread::yield_now();
            }
        } else {
            false
        }
    }

    pub fn reset_all(&self) {
        for fence in self.fences.values() {
            fence.reset();
        }
        for sem in self.semaphores.values() {
            sem.reset();
        }
        for event in self.events.values() {
            event.reset();
        }
    }

    pub fn fence_count(&self) -> usize {
        self.fences.len()
    }

    pub fn semaphore_count(&self) -> usize {
        self.semaphores.len()
    }

    pub fn event_count(&self) -> usize {
        self.events.len()
    }
}
