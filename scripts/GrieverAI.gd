extends CharacterBody3D

# Griever AI — State Machine (Godot 4.3)
# Не LLM, не нейросеть. Нормальный Game AI.

enum STATE { PATROL, CHASE, ATTACK }

@export var patrol_points: Array[Vector3] = []
@export var vision_range: float = 10.0
@export var vision_angle_deg: float = 60.0
@export var attack_range: float = 2.0
@export var chase_speed: float = 4.5
@export var patrol_speed: float = 2.0

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var sight_ray: RayCast3D = $SightRayCast
@onready var attack_area: Area3D = $AttackArea
@onready var anim_player: AnimationPlayer = $AnimationPlayer

var current_state: STATE = STATE.PATROL
var current_patrol_index: int = 0
var player_ref: Node3D = null

func _ready() -> void:
	nav_agent.velocity_computed.connect(_on_nav_velocity_computed)
	# Найти игрока в сцене или через группа
	player_ref = get_tree().get_first_node_in_group("player")
	# Начальная точка патруля
	if patrol_points.size() > 0:
		nav_agent.target_location = patrol_points[0]

func _physics_process(delta: float) -> void:
	# Если игрок не найден — просто патруль
	if player_ref == null:
		player_ref = get_tree().get_first_node_in_group("player")

	match current_state:
		STATE.PATROL:
			_update_patrol(delta)
		STATE.CHASE:
			_update_chase(delta)
		STATE.ATTACK:
			_update_attack(delta)

func _update_patrol(delta: float) -> void:
	if nav_agent.is_target_reached():
		current_patrol_index = (current_patrol_index + 1) % patrol_points.size()
		nav_agent.target_location = patrol_points[current_patrol_index]
	# Движение
	if nav_agent.is_navigation_finished():
		velocity = Vector3.ZERO
	else:
		velocity = nav_agent.get_final_velocity().normalized() * patrol_speed

	# Проверка зрения
	if can_see_player():
		current_state = STATE.CHASE

func _update_chase(delta: float) -> void:
	if player_ref == null:
		current_state = STATE.PATROL
		return
	nav_agent.target_location = player_ref.global_position
	if nav_agent.is_navigation_finished():
		velocity = Vector3.ZERO
	else:
		velocity = nav_agent.get_final_velocity().normalized() * chase_speed

	var dist := global_position.distance_to(player_ref.global_position)
	if dist > vision_range * 1.5:
		current_state = STATE.PATROL
	elif dist < attack_range:
		current_state = STATE.ATTACK

func _update_attack(delta: float) -> void:
	# Анимация атаки; урон игроку через Area3D или сигнал
	velocity = Vector3.ZERO
	if anim_player != null:
		anim_player.play("attack")
	# Возврат в преследование после атаки
	await get_tree().create_timer(1.0).timeout
	current_state = STATE.CHASE

func can_see_player() -> bool:
	if player_ref == null:
		return false
	var to_player := (player_ref.global_position - global_position).normalized()
	# Угол
	var forward := global_transform.basis.z.normalized()
	var angle := forward.angle_to(to_player)
	if angle > deg_to_rad(vision_angle_deg / 2.0):
		return false
	# Линия видимости
	sight_ray.target_position = player_ref.global_position - global_position
	sight_ray.force_raycast_update()
	if sight_ray.is_colliding():
		var collider := sight_ray.get_collider()
		if collider == player_ref or collider.is_in_group("player"):
			return true
	else:
		# Нет преграды
		return true
	return false

func _on_nav_velocity_computed(safe_velocity: Vector3) -> void:
	# Godot 4.3 NavigationAgent3D: velocity_computed сигнал
	# Но мы уже используем get_final_velocity() в _update
	pass

func _on_attack_area_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		# Урон или тревога
		body.emit_signal("took_damage", 10.0)
