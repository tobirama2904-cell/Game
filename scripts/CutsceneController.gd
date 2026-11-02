extends Node3D

@export var skip_key: String = "ui_accept"
@export var duration: float = 45.0

func _ready() -> void:
	$AnimationPlayer.play("intro")
	$AudioStreamPlayer3D.play()

func _process(delta: float) -> void:
	if Input.is_action_just_pressed(skip_key):
		skip_cutscene()

func skip_cutscene() -> void:
	get_tree().change_scene_to_file("res://scenes/glade.tscn")
