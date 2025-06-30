// Copyright (c) 1998-2025 Scott Russell
// SPDX-License-Identifier: MIT

use bevy::prelude::*;

pub fn setup(mut commands: Commands, asset_server: Res<AssetServer>) {
    commands.spawn(Camera2dBundle::default());

    commands.spawn(
        TextBundle::from_section(
            "🔌 Waiting for clock.tick...",
            TextStyle {
                font: asset_server.load("fonts/fa-6-regular-400.otf"),
                font_size: 40.0,
                color: Color::WHITE,
            },
        )
        .with_style(Style {
            position_type: PositionType::Absolute,
            top: Val::Px(20.0),
            left: Val::Px(20.0),
            ..Default::default()
        }),
    );
}
