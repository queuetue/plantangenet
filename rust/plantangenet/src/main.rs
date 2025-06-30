// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use bevy::prelude::*;
use plantangenet::nats::listener::start_tick_listener;
use plantangenet::ClockState;
use plantangenet::SharedClockState;
use plantangenet::systems::setup::setup;
use plantangenet::systems::update_display::update_display;
use std::sync::{Arc, Mutex};

fn main() {
    let shared_state = SharedClockState(Arc::new(Mutex::new(ClockState::default())));
    {
        let state_clone = shared_state.clone();
        std::thread::spawn(move || {
            pollster::block_on(start_tick_listener(state_clone));
        });
    }

    App::new()
        .insert_resource(shared_state)
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "🌀 Plantangenet Player".into(),
                resolution: (640., 360.).into(),
                ..default()
            }),
            ..default()
        }))
        .add_systems(Startup, setup )
        .add_systems(Update, update_display)
        .run();
}
