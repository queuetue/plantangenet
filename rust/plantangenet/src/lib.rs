// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use serde::Deserialize;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;

#[derive(Debug, Deserialize, Clone)]
pub struct TickMessage {
    pub id: String,
    pub short_id: String,
    pub event_type: String,
    pub stamp: f64,
    pub interval: f64,
    pub paused: bool,
    pub stepping: bool,
    pub start_time: f64,
    pub namespace: String,
    pub backpressure: bool,
    pub wall_time: Vec<i32>,
    pub current_choice: Option<String>,
    pub transport: Vec<String>,
    pub disposition: Option<String>,
    pub connected: bool,
    pub accumulators: HashMap<String, AccumulatorData>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct AccumulatorData {
    pub interval: f64,
    pub elapsed: f64,
    pub cycles: u64,
    pub running: bool,
    pub repeating: bool,
}

#[derive(Default, Clone)]
pub struct ClockState {
    pub stamp: f64,
    pub paused: bool,
    pub last_update: Option<Instant>,
}

#[derive(bevy::prelude::Resource, Clone)]
pub struct SharedClockState(pub Arc<Mutex<ClockState>>);

pub mod nats;
pub mod systems;
pub mod conductor;
pub mod resources;
