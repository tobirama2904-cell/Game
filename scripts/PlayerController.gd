extends CharacterBody3D

@export var speed: float = 5.0
@export var jump_velocity: float = 8.0
@export var gravity: float = 20.0
@export var camera_offset: Vector3 = Vector3(0.0, 3.5, 5.0)

@onready var camera_3d: Camera3D = $Camera3D
@onready var animation_player: AnimationPlayer = $AnimationPlayer

var is_touching: bool = false
var touch_start_pos: Vector2 = Vector2.ZERO
var touch_current_pos: Vector2 = Vector2.ZERO
var mobile_direction: Vector2 = Vector2.ZERO

func _ready():
	if camera_3d == null:
		push_warning("Camera3D not found in player scene.")
	# Mobile: enable touch input
	if OS.has_feature("mobile"):
		InputMap.action_add_event("jump", InputEventScreenTouch.new())

func _physics_process(delta: float) -> void:
	# Gravity
	if not is_on_floor():
		velocity.y -= gravity * delta

	# Keyboard / Gamepad movement
	var input_dir := Vector3(
		(Input.get_action_strength("move_right") - Input.get_action_strength("move_left")),
		0.0,
		(Input.get_action_strength("move_back") - Input.get_action_strength("move_forward"))
	).normalized()

	# Mobile touch movement (drag-based)
	if mobile_direction != Vector2.ZERO:
		input_dir = Vector3(mobile_direction.x, 0.0, -mobile_direction.y).normalized()

	# Apply velocity on X/Z
	if input_dir != Vector3.ZERO:
		velocity.x = input_dir.x * speed
		velocity.z = input_dir.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed)
		velocity.z = move_toward(velocity.z, 0.0, speed)

	# Jump
	if (Input.is_action_just_pressed("jump") or Input.is_action_pressed("jump")) and is_on_floor():
		velocity.y = jump_velocity

	# Move
	move_and_slide()

	# Animation triggers (basic)
	if animation_player != null:
		if not is_on_floor():
			animation_player.play("jump")
		elif input_dir != Vector3.ZERO:
			animation_player.play("run")
		else:
			animation_player.play("idle")

	# Camera follow (smooth, behind player)
	if camera_3d != null:
		var target_pos := global_position + camera_offset
		camera_3d.global_position = camera_3d.global_position.lerp(target_pos, 0.1)
		camera_3d.look_at(global_position + Vector3(0, 1.5, 0))

func _input(event: InputEvent) -> void:
	# Mobile drag-based movement
	if event is InputEventScreenTouch:
		if event.pressed:
			is_touching = true
			touch_start_pos = event.position
			touch_current_pos = event.position
		else:
			is_touching = false
			mobile_direction = Vector2.ZERO

	if event is InputEventScreenDrag:
		if is_touching:
			touch_current_pos = event.position
			var delta := touch_current_pos - touch_start_pos
			# Scale for mobile sensitivity
			mobile_direction = (delta / 100.0).limit_length(1.0)

	# Interact (E key or touch button)
	if Input.is_action_just_pressed("interact"):
		raycast_interact()

func raycast_interact() -> void:
	# Simple forward raycast for interaction
	var space_state := get_world_3d().direct_space_state
	var from := global_position + Vector3(0.0, 1.5, 0.0)
	var to := from + global_transform.basis.z * 2.0
	var result := space_state.intersect_ray(from, to, [self])
	if result:
		var collider := result.collider
		if collider.has_method("interact"):
			collider.interact()
