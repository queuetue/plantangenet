// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use crate::SharedClockState;
use async_nats::ConnectOptions;
use futures_util::stream::StreamExt;
use crate::conductor::tick::handle_tick;

pub async fn start_tick_listener(state: SharedClockState) {
    let client = ConnectOptions::new()
        .connect("nats://127.0.0.1:4222")
        .await
        .expect("failed to connect to NATS");

    let mut subscriber = client
        .subscribe("clock.tick".into())
        .await
        .expect("failed to subscribe");

    println!("Listening for clock.tick messages...");

    while let Some(message) = subscriber.next().await {
        if let Err(e) = handle_tick(&message, &state).await {
            eprintln!("Error handling tick message: {}", e);
        }
    }
}
