// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use bevy::prelude::*;
use crate::SharedClockState;

pub fn update_display(
    clock_state: Res<SharedClockState>,
    mut query: Query<&mut Text>,
) {
    if let Ok(state) = clock_state.0.lock() {
        if let Ok(mut text) = query.get_single_mut() {
            text.sections[0].value = format!("🕒 {:.2} | {}", state.stamp, if state.paused { "⏸" } else { "▶️" });
        }
    }
}
