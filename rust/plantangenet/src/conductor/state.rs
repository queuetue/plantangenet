// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use crate::{ClockState, SharedClockState};
use std::sync::MutexGuard;

pub fn update_clock(state: &SharedClockState, stamp: f64, paused: bool) {
    if let Ok(mut lock) = state.0.lock() {
        lock.stamp = stamp;
        lock.paused = paused;
        lock.last_update = Some(std::time::Instant::now());
    }
}

pub fn read_clock(state: &SharedClockState) -> Option<MutexGuard<'_, ClockState>> {
    state.0.lock().ok()
}
