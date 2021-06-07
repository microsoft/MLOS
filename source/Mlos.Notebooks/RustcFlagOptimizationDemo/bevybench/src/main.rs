use bevy::{
    prelude::*,
    render::{
        mesh::shape,
    },
};
static mut FRAMES:i32 = 0;
fn main() {
    App::build()
        .add_resource(Msaa { samples: 8 })
        .add_default_plugins()
        .add_startup_system(setup.system())
        .add_system(rotator_system.system())
        .add_system(rotatel.system())
        .run();
}

struct CameraOperator;
struct Rotator;

/// rotates the parent, which will result in the child also rotating
fn rotator_system(time: Res<Time>, mut query: Query<(&Rotator, &mut Rotation)>) {
    for (_rotator, mut rotation) in &mut query.iter() {
        rotation.0 = rotation.0 * Quat::from_rotation_x(3.0 * time.delta_seconds);
    }
    unsafe{
        FRAMES = FRAMES + 1;
        if FRAMES >= 240 {
            std::process::exit(0);
        }
    }
}


fn setup(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    commands
        .spawn(PbrComponents {
            mesh: meshes.add(Mesh::from(shape::Plane { size: 40.0 })),
            material: materials.add(Color::rgb(0.1, 0.3, 0.1).into()),
            ..Default::default()
        })
        .spawn(LightComponents {
            translation: Translation::new(8.0, 8.0, 4.0),
            ..Default::default()
        })
        .spawn(Camera3dComponents {
            transform: Transform::new_sync_disabled(Mat4::face_toward(
                Vec3::new(-3.0, 5.0, 8.0),
                Vec3::new(0.0, 0.0, 0.0),
                Vec3::new(0.0, 1.0, 0.0),
            )),
            ..Default::default()
        })
        .with(CameraOperator);

    for x in -500..500 {
        commands.spawn(PbrComponents {
            mesh: meshes.add(Mesh::from(shape::Cube { size: 1.0 })),
            material: materials.add(Color::rgb(0.5, 0.4, 0.3).into()),
            translation: Translation::new(x as f32, 1.0, 0.0),
            ..Default::default()
        }).with(Rotator);
    }

}

fn rotatel(time: Res<Time>, mut query: Query<(&CameraOperator, &mut Transform)>) {
    
    for (_camera_operator, mut transform) in &mut query.iter() {
        //println!("trans {},{}", time.delta_seconds, transform.value);
        transform.value =  Mat4::face_toward(
            Vec3::new((time.seconds_since_startup as f32).cos()*20.0,4.0,(time.seconds_since_startup as f32).sin()*20.0),
            Vec3::new(0.0, 0.0, 0.0),
            Vec3::new(0.0, 1.0, 0.0),
        );// .mul_vec4(Vec4::zero());
     //   rotation.0 = rotation.0 * Quat::from_rotation_x(3.0 * time.delta_seconds);
    }
    
}


