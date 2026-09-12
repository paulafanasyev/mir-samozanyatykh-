# ==========================================================
# 3D АВАТАР: ДЕВУШКА-КОНСУЛЬТАНТ (25 ЛЕТ, БРЮНЕТКА)
# Деловая одежда, бейджик "Мир Самозанятых"
# Полный риг, морфы мимики, анимации для Android
# ==========================================================

import bpy
import math
import os
from mathutils import Vector, Quaternion, Matrix

OUT_DIR = os.path.join(os.path.expanduser("~"), "office_avatar_assets")
os.makedirs(OUT_DIR, exist_ok=True)

FPS = 30
scene = bpy.context.scene
scene.render.fps = FPS

collection = bpy.data.collections.new("OfficeGirl_Collection")
scene.collection.children.link(collection)

body_parts = []

# --- 1. МАТЕРИАЛЫ ---

def create_mat(name, color, roughness=0.6, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    return mat

# Палитра
mat_skin = create_mat("M_Skin", (0.94, 0.76, 0.67), roughness=0.55)
mat_hair = create_mat("M_Hair_Brunette", (0.08, 0.04, 0.02), roughness=0.35, metallic=0.1)
mat_eyes_blue = create_mat("M_Eyes_Blue", (0.05, 0.45, 0.95), roughness=0.15)
mat_eyes_white = create_mat("M_Eyes_White", (0.95, 0.95, 0.95), roughness=0.2)
mat_pupil = create_mat("M_Pupil", (0.01, 0.01, 0.01), roughness=0.1)
mat_lips = create_mat("M_Lips", (0.85, 0.32, 0.35), roughness=0.3)

mat_blazer = create_mat("M_Blazer_Navy", (0.04, 0.07, 0.16), roughness=0.7) # Тёмно-синий пиджак
mat_blouse = create_mat("M_Blouse_White", (0.92, 0.94, 0.96), roughness=0.6) # Шёлковая белая блузка
mat_trousers = create_mat("M_Trousers_Navy", (0.04, 0.07, 0.16), roughness=0.7) # Брюки в тон
mat_shoes = create_mat("M_Shoes_Black", (0.02, 0.02, 0.02), roughness=0.2, metallic=0.2) # Лодочки

# Бейджик
mat_badge_bg = create_mat("M_Badge_BG", (0.95, 0.95, 0.98), roughness=0.3)
mat_badge_gold = create_mat("M_Badge_Gold", (0.95, 0.70, 0.15), roughness=0.3, metallic=0.8)
mat_badge_text = create_mat("M_Badge_Text", (0.02, 0.25, 0.65), roughness=0.4) # Корпоративный синий
mat_lanyard = create_mat("M_Lanyard", (0.02, 0.45, 0.85), roughness=0.5) # Лента на шею

# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ГЕОМЕТРИИ ---

def register_part(obj, name, mat, bone_name, smooth=True):
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
        
    if obj.type == 'MESH' and smooth:
        for f in obj.data.polygons:
            f.use_smooth = True
            
    vg = obj.vertex_groups.new(name=bone_name)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    
    body_parts.append(obj)
    return obj

def add_sphere(name, loc, scale, mat, bone_name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    return register_part(obj, name, mat, bone_name)

def add_cylinder(name, start, end, radius, mat, bone_name):
    s, e = Vector(start), Vector(end)
    dir_v = e - s
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=dir_v.length, location=(s + e)/2)
    obj = bpy.context.object
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = dir_v.to_track_quat('Z', 'Y')
    return register_part(obj, name, mat, bone_name)

def add_box(name, loc, size, mat, bone_name, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return register_part(obj, name, mat, bone_name, smooth=False)

# --- 3. СКЕЛЕТ (РИГ) ---

REST_BONES = {
    "root": ((0,0,0), (0,0,0.15), None),
    "pelvis": ((0,0,0.92), (0,0,1.02), "root"),
    "spine": ((0,0,1.02), (0,0,1.22), "pelvis"),
    "chest": ((0,0,1.22), (0,0,1.44), "spine"),
    "neck": ((0,0,1.44), (0,0,1.52), "chest"),
    "head": ((0,0,1.52), (0,0,1.78), "neck"),
}

for s, sfx in [(-1, "L"), (1, "R")]:
    REST_BONES[f"upper_arm.{sfx}"] = ((s*0.18, 0, 1.38), (s*0.32, 0, 1.15), "chest")
    REST_BONES[f"forearm.{sfx}"] = ((s*0.32, 0, 1.15), (s*0.38, -0.02, 0.92), f"upper_arm.{sfx}")
    REST_BONES[f"hand.{sfx}"] = ((s*0.38, -0.02, 0.92), (s*0.40, -0.02, 0.82), f"forearm.{sfx}")
    
    REST_BONES[f"thigh.{sfx}"] = ((s*0.11, 0, 0.92), (s*0.12, -0.02, 0.52), "pelvis")
    REST_BONES[f"shin.{sfx}"] = ((s*0.12, -0.02, 0.52), (s*0.12, 0, 0.14), f"thigh.{sfx}")
    REST_BONES[f"foot.{sfx}"] = ((s*0.12, 0, 0.14), (s*0.12, -0.16, 0.04), f"shin.{sfx}")

arm_data = bpy.data.armatures.new("OfficeGirl_Skeleton")
rig = bpy.data.objects.new("OfficeGirl_Rig", arm_data)
collection.objects.link(rig)
rig.show_in_front = True

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')

for b_name, (h, t, p) in REST_BONES.items():
    bone = arm_data.edit_bones.new(b_name)
    bone.head, bone.tail = h, t
    if p:
        bone.parent = arm_data.edit_bones[p]
        bone.use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# --- 4. СОЗДАНИЕ ТЕЛА И ОДЕЖДЫ ---

# Торс и таз (Блузка + Пиджак)
add_sphere("Hips_Trousers", (0, 0, 0.94), (0.17, 0.12, 0.14), mat_trousers, "pelvis")
add_cylinder("Waist_Blouse", (0, 0, 0.98), (0, 0, 1.24), 0.13, mat_blouse, "spine")
add_sphere("Chest_Blouse", (0, -0.01, 1.28), (0.16, 0.13, 0.14), mat_blouse, "chest")

# Пиджак (Лацканы и плечи)
add_box("Blazer_Back", (0, 0.02, 1.26), (0.34, 0.20, 0.38), mat_blazer, "chest", 0.04)
add_box("Blazer_Lapel_L", (-0.11, -0.08, 1.28), (0.08, 0.04, 0.22), mat_blazer, "chest", 0.02)
add_box("Blazer_Lapel_R", (0.11, -0.08, 1.28), (0.08, 0.04, 0.22), mat_blazer, "chest", 0.02)

# Шея и Голова
add_cylinder("Neck", (0, 0, 1.42), (0, 0, 1.54), 0.052, mat_skin, "neck")
add_sphere("Head_Base", (0, -0.01, 1.63), (0.125, 0.135, 0.15), mat_skin, "head")
add_sphere("Chin", (0, -0.06, 1.54), (0.055, 0.06, 0.05), mat_skin, "head") # Изящный подбородок

# Причёска (Шикарные тёмно-каштановые волосы, спадающие на плечи)
add_sphere("Hair_Top", (0, 0.02, 1.70), (0.14, 0.155, 0.13), mat_hair, "head")
add_sphere("Hair_Back", (0, 0.08, 1.58), (0.15, 0.14, 0.22), mat_hair, "head")
# Боковые пряди
for side in (-1, 1):
    add_cylinder("Hair_Side", (side*0.13, 0.01, 1.66), (side*0.14, -0.03, 1.40), 0.045, mat_hair, "head")
    add_sphere("Hair_End", (side*0.14, -0.03, 1.38), (0.045, 0.045, 0.06), mat_hair, "head")
    add_sphere("Ear", (side*0.125, 0.01, 1.62), (0.025, 0.035, 0.045), mat_skin, "head")

# --- 5. БЕЙДЖИК "МИР САМОЗАНЯТЫХ" ---

# Лента бейджика (идёт вокруг шеи)
add_cylinder("Lanyard_L", (-0.06, -0.07, 1.45), (-0.07, -0.11, 1.28), 0.008, mat_lanyard, "chest")
add_cylinder("Lanyard_R", (0.06, -0.07, 1.45), (0.05, -0.11, 1.28), 0.008, mat_lanyard, "chest")

# Пластиковая карточка бейджика на груди (слева)
badge_card = add_box("Badge_Card", (-0.07, -0.125, 1.24), (0.095, 0.008, 0.125), mat_badge_bg, "chest", 0.006)
add_box("Badge_Clip", (-0.07, -0.123, 1.305), (0.025, 0.012, 0.015), mat_badge_gold, "chest", 0.003)
add_box("Badge_Photo", (-0.09, -0.130, 1.25), (0.032, 0.003, 0.04), mat_badge_gold, "chest", 0.002)

# 3D Текст на бейджике "Мир Самозанятых"
bpy.ops.object.text_add(location=(-0.07, -0.132, 1.25))
txt_obj = bpy.context.object
txt_obj.name = "Badge_Text_Mesh"
txt_obj.data.body = "МИР\nСАМОЗАНЯТЫХ"
txt_obj.data.align_x = 'CENTER'
txt_obj.data.align_y = 'CENTER'
txt_obj.data.size = 0.011
txt_obj.data.extrude = 0.002
txt_obj.scale = (0.9, 0.9, 0.9)
bpy.ops.object.convert(target='MESH')
register_part(txt_obj, "Badge_Text_Mesh", mat_badge_text, "chest", smooth=False)

# Руки и Ноги
for s, sfx in [(-1, "L"), (1, "R")]:
    u_arm = f"upper_arm.{sfx}"
    f_arm = f"forearm.{sfx}"
    h_arm = f"hand.{sfx}"
    
    # Рукава пиджака и кисти
    add_sphere(f"Shoulder.{sfx}", (s*0.18, 0, 1.38), (0.065, 0.065, 0.07), mat_blazer, u_arm)
    add_cylinder(f"Sleeve.{sfx}", (s*0.18, 0, 1.38), (s*0.32, 0, 1.15), 0.052, mat_blazer, u_arm)
    add_cylinder(f"Forearm.{sfx}", (s*0.32, 0, 1.15), (s*0.37, -0.02, 0.94), 0.042, mat_skin, f_arm)
    add_sphere(f"Hand.{sfx}", (s*0.38, -0.02, 0.90), (0.038, 0.025, 0.055), mat_skin, h_arm)

    # Деловые брюки и туфли на небольшом каблуке
    t_leg = f"thigh.{sfx}"
    s_leg = f"shin.{sfx}"
    f_leg = f"foot.{sfx}"
    
    add_cylinder(f"Thigh.{sfx}", (s*0.11, 0, 0.92), (s*0.12, -0.02, 0.52), 0.068, mat_trousers, t_leg)
    add_cylinder(f"Shin.{sfx}", (s*0.12, -0.02, 0.52), (s*0.12, 0, 0.14), 0.052, mat_trousers, s_leg)
    
    # Туфли-лодочки
    add_box(f"Shoe.{sfx}", (s*0.12, -0.06, 0.07), (0.085, 0.18, 0.065), mat_shoes, f_leg, 0.015)
    add_cylinder(f"Heel.{sfx}", (s*0.12, 0.01, 0.04), (s*0.12, 0.01, 0.09), 0.015, mat_shoes, f_leg)

# Объединение мешей тела
bpy.ops.object.select_all(action='DESELECT')
for p in body_parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = body_parts[0]
bpy.ops.object.join()
body_main = bpy.context.object
body_main.name = "OfficeGirl_Body"

body_main.parent = rig
mod_b = body_main.modifiers.new("Armature", 'ARMATURE')
mod_b.object = rig
mod_b.use_vertex_groups = True

# --- 6. ЛИЦО, ГОЛУБЫЕ ГЛАЗА И МОРФЫ (МИМИКА) ---

face_verts = []
face_polys = []
face_tags = []

FACE_Y = -0.138

def f_v(x, z, tag):
    idx = len(face_verts)
    face_verts.append((x, FACE_Y, z))
    face_tags.append(tag)
    return idx

# Красивые выразительные голубые глаза (крупные, мультяшные)
for side, sx in [(-1, -0.048), (1, 0.048)]:
    # Склера (белок)
    c_eye = f_v(sx, 1.635, "eye_white")
    ring_w = []
    for i in range(16):
        a = math.pi * 2 * i / 16
        ring_w.append(f_v(sx + 0.026*math.cos(a), 1.635 + 0.022*math.sin(a), "eye_white"))
    for i in range(16):
        face_polys.append((c_eye, ring_w[i], ring_w[(i+1)%16]))

    # Радужка (голубая)
    c_iris = f_v(sx, 1.635, "iris")
    ring_i = []
    for i in range(16):
        a = math.pi * 2 * i / 16
        ring_i.append(f_v(sx + 0.018*math.cos(a), 1.635 + 0.018*math.sin(a), "iris"))
    for i in range(16):
        face_polys.append((c_iris, ring_i[i], ring_i[(i+1)%16]))

# Губы
m_outer, m_inner = [], []
for i in range(24):
    a = math.pi * 2 * i / 24
    m_outer.append(f_v(0.042*math.cos(a), 1.558 + 0.012*math.sin(a), "mouth"))
    m_inner.append(f_v(0.035*math.cos(a), 1.558 + 0.004*math.sin(a), "mouth"))
for i in range(24):
    j = (i+1)%24
    face_polys.append((m_outer[i], m_outer[j], m_inner[j], m_inner[i]))

# Аккуратные брови
for sx in [-0.048, 0.048]:
    ids = [f_v(sx-0.025, 1.675, "brow"), f_v(sx+0.025, 1.675, "brow"),
           f_v(sx+0.025, 1.682, "brow"), f_v(sx-0.025, 1.682, "brow")]
    face_polys.append(tuple(ids))

f_mesh = bpy.data.meshes.new("OfficeGirl_FaceMesh")
f_mesh.from_pydata(face_verts, [], face_polys)
f_mesh.update()

face_obj = bpy.data.objects.new("OfficeGirl_Face", f_mesh)
collection.objects.link(face_obj)

# Назначение материалов лица
face_obj.data.materials.append(mat_lips) # 0
face_obj.data.materials.append(mat_eyes_blue) # 1
face_obj.data.materials.append(mat_eyes_white) # 2
face_obj.data.materials.append(mat_hair) # 3 (брови)

for poly in face_obj.data.polygons:
    v_tag = face_tags[poly.vertices[0]]
    if "iris" in v_tag: poly.material_index = 1
    elif "eye_white" in v_tag: poly.material_index = 2
    elif "brow" in v_tag: poly.material_index = 3
    else: poly.material_index = 0

face_obj.parent = rig
vg_f = face_obj.vertex_groups.new(name="head")
vg_f.add(list(range(len(face_verts))), 1.0, 'REPLACE')
mod_f = face_obj.modifiers.new("Armature", 'ARMATURE')
mod_f.object = rig

# Морфы мимики для синхронизации речи и эмоций
face_obj.shape_key_add(name="Basis")
MORPHS = ["MouthOpen", "Happy", "Sad", "Angry", "Blink"]

for m_name in MORPHS:
    sk = face_obj.shape_key_add(name=m_name)
    for i, v in enumerate(sk.data):
        x, y, z = face_verts[i]
        tag = face_tags[i]
        nx, nz = x, z
        
        if m_name == "MouthOpen" and tag == "mouth":
            idx = i % 24
            nz += 0.025 * math.sin(idx * 0.26)
        elif m_name == "Happy":
            if tag == "mouth": nz += 0.018 * (x/0.042)**2 + 0.004
            elif "eye" in tag or tag == "iris": nz = 1.635 + (z-1.635)*0.85
        elif m_name == "Sad":
            if tag == "mouth": nz -= 0.015 * (x/0.042)**2
            elif tag == "brow": nz += 0.015
        elif m_name == "Angry":
            if tag == "brow": nz += 0.02 * (1 - abs(x)/0.05)
        elif m_name == "Blink" and ("eye" in tag or tag == "iris"):
            nz = 1.635 + (z-1.635)*0.08
            
        v.co = (nx, y, nz)

# --- 7. АНИМАЦИИ (ЗАРЯДКА + ПРЕЗЕНТАЦИЯ) ---

rig.animation_data_create()
actions = []

ANIM_LIST = [
    ("Idle", 4.0),
    ("Talk", 4.0),
    ("Wave", 3.0),
    ("RaiseArms", 6.0),
    ("Squat", 4.0),
    ("March", 4.0)
]

def reset_pose():
    for pb in rig.pose.bones:
        pb.location = (0,0,0)
        pb.rotation_quaternion = (1,0,0,0)

def rot_bone(name, axis, deg):
    pb = rig.pose.bones[name]
    q = Quaternion(axis, math.radians(deg))
    pb.rotation_quaternion = q

def apply_pose(clip, t):
    reset_pose()
    
    # Дыхание в Idle
    if clip == "Idle":
        wave = math.sin(2 * math.pi * t)
        rot_bone("chest", (1,0,0), 2.0 * wave)
        rot_bone("head", (0,1,0), 3.0 * wave)

    elif clip == "Talk":
        # Презентация: активная жестикуляция правой рукой
        wave = math.sin(4 * math.pi * t)
        rot_bone("head", (0,0,1), 4.0 * math.sin(2 * math.pi * t))
        rot_bone("upper_arm.R", (1,0,0), 45 + 15 * wave)
        rot_bone("forearm.R", (0,1,0), 30 + 20 * wave)
        rot_bone("upper_arm.L", (1,0,0), 15)

    elif clip == "Wave":
        # Приветственный взмах
        rot_bone("upper_arm.R", (1,0,0), 110)
        rot_bone("forearm.R", (0,1,0), 40 + 35 * math.sin(8 * math.pi * t))
        rot_bone("head", (0,0,1), -5)

    elif clip == "RaiseArms":
        # Зарядка: подъём рук
        pulse = 0.5 - 0.5 * math.cos(2 * math.pi * t)
        for s in ["L", "R"]:
            rot_bone(f"upper_arm.{s}", (1,0,0), 160 * pulse)
            rot_bone(f"forearm.{s}", (1,0,0), 15 * pulse)

    elif clip == "Squat":
        # Приседания
        pulse = 0.5 - 0.5 * math.cos(2 * math.pi * t)
        rig.pose.bones["pelvis"].location.z = -0.30 * pulse
        rot_bone("chest", (1,0,0), 18 * pulse)
        for s in ["L", "R"]:
            rot_bone(f"thigh.{s}", (1,0,0), -55 * pulse)
            rot_bone(f"shin.{s}", (1,0,0), 75 * pulse)
            rot_bone(f"upper_arm.{s}", (1,0,0), 70 * pulse) # Руки вперёд для баланса

    elif clip == "March":
        # Шаги на месте
        phase = 4 * math.pi * t
        for s_idx, s in [(-1, "L"), (1, "R")]:
            lift = max(0, s_idx * math.sin(phase))
            rot_bone(f"thigh.{s}", (1,0,0), -40 * lift)
            rot_bone(f"shin.{s}", (1,0,0), 55 * lift)
            rot_bone(f"upper_arm.{s}", (1,0,0), 25 * s_idx * math.sin(phase))

for name, duration in ANIM_LIST:
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data.action = act
    
    frames = int(duration * FPS)
    for f in range(frames + 1):
        scene.frame_set(f + 1)
        apply_pose(name, f / frames)
        for pb in rig.pose.bones:
            pb.keyframe_insert("location", frame=f+1)
            pb.keyframe_insert("rotation_quaternion", frame=f+1)
            
    actions.append((name, act))
    rig.animation_data.action = None

for name, act in actions:
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, 1, act)
    strip.blend_type = 'REPLACE'

# --- 8. ЭКСПОРТ В GLB ---

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
body_main.select_set(True)
face_obj.select_set(True)
bpy.context.view_layer.objects.active = rig

filepath = os.path.join(OUT_DIR, "OfficeGirl.glb")
bpy.ops.export_scene.gltf(
    filepath=filepath,
    export_format='GLB',
    use_selection=True,
    export_animations=True,
    export_morph=True,
    export_force_sampling=True,
    export_animation_mode='NLA_TRACKS',
    export_yup=True
)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "OfficeGirl.blend"))

print(f"\n==========================================")
print(f"МОДЕЛЬ УСПЕШНО СОЗДАНА!")
print(f"GLB Файл: {filepath}")
print(f"Папка: {OUT_DIR}")
print(f"==========================================")
