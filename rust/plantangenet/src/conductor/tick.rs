// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT
use async_nats::Message;
use crate::{TickMessage, SharedClockState};
use crate::conductor::state::update_clock;
use anyhow::Result;

pub async fn handle_tick(msg: &Message, shared: &SharedClockState) -> Result<()> {
    let tick: TickMessage = serde_json::from_slice(&msg.payload)?;
    update_clock(shared, tick.stamp, tick.paused);
    Ok(())
}