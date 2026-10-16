"""
Placeholder head for the Stretchy Head template.

A generic cartoon head generated as a quad grid (longitude x latitude), so that
every row is an edge loop. The mouth is cut along one of those rows and the two
sides of the cut carry different jaw weights, exactly as ASSET-SPEC.md asks.
Everything is procedural: geometry, texture, jaw/hair/eye weights and the
"Surprise" shape key. Nothing here comes from a scan or a person.

Coordinates: head about 1 unit tall, centred on the origin, +y up, +z toward the
viewer, mirror plane x = 0.

Outputs (in the folder given on the command line):
  head.glb       mesh "Head" + "MouthInterior", custom attributes, shape keys, texture embedded
  head.json      the numbers the page needs (pivot, cavity, eyes, skin, split lines)
  basecolor.jpg  the same texture as a separate file
"""
import json, struct, sys, os, io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)

# ---------------- proportions (generic cartoon) ----------------
EYE_Y, EYE_X, EYE_A, EYE_B = 0.05, 0.14, 0.074, 0.05     # eye centres and opening semi-axes
BROW_Y = 0.165
NOSE_Y = -0.07
MOUTH_Y, MOUTH_HW = -0.19, 0.115                           # the cut row and the half-width of the slit
CHIN_Y = -0.46
HAIRLINE_Y = 0.26

def sm(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def blob(P, c, r):
    d = (P - np.asarray(c)) / np.asarray(r)
    return np.exp(-2.0 * (d ** 2).sum(-1))

def sphere_dirs(u, v):
    th = (u - 0.5) * 2 * np.pi; ph = v * np.pi
    return np.stack([np.sin(ph) * np.sin(th), np.cos(ph), np.sin(ph) * np.cos(th)], -1)

def base_radius(d):
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    rx, ry, rz = 0.415, 0.485, 0.43
    n = 2.15
    r = (np.abs(x / rx) ** n + np.abs(y / ry) ** n + np.abs(z / rz) ** n) ** (-1.0 / n)
    p = d * r[..., None]
    below = sm((-p[..., 1] - 0.08) / 0.32)                      # jaw narrows under the cheekbones
    r = r * (1.0 - below * 0.15 * sm(np.abs(p[..., 0]) / 0.30))
    return r

def head_radius(d):
    r0 = base_radius(d)
    p = d * r0[..., None]
    f = 0
    f -= 0.040 * (blob(p, [-EYE_X, EYE_Y, 0.33], [0.11, 0.075, 0.16]) + blob(p, [EYE_X, EYE_Y, 0.33], [0.11, 0.075, 0.16]))   # sockets
    f += 0.030 * (blob(p, [-EYE_X, EYE_Y, 0.36], [0.075, 0.05, 0.12]) + blob(p, [EYE_X, EYE_Y, 0.36], [0.075, 0.05, 0.12]))   # eyeball domes
    f += 0.026 * (blob(p, [-EYE_X, BROW_Y, 0.33], [0.12, 0.045, 0.13]) + blob(p, [EYE_X, BROW_Y, 0.33], [0.12, 0.045, 0.13]))  # brow ridges
    f += 0.055 * (blob(p, [-0.21, -0.11, 0.26], [0.14, 0.13, 0.17]) + blob(p, [0.21, -0.11, 0.26], [0.14, 0.13, 0.17]))        # cheeks
    f += 0.110 * blob(p, [0, NOSE_Y + 0.02, 0.36], [0.06, 0.09, 0.10]) + 0.075 * blob(p, [0, NOSE_Y - 0.03, 0.39], [0.058, 0.05, 0.08])
    f += 0.035 * (blob(p, [-0.06, NOSE_Y - 0.045, 0.35], [0.04, 0.035, 0.07]) + blob(p, [0.06, NOSE_Y - 0.045, 0.35], [0.04, 0.035, 0.07]))
    f += 0.030 * blob(p, [0, MOUTH_Y + 0.045, 0.33], [0.125, 0.032, 0.12]) + 0.028 * blob(p, [0, MOUTH_Y - 0.05, 0.325], [0.11, 0.035, 0.12])   # lips
    f += 0.040 * blob(p, [0, -0.38, 0.20], [0.15, 0.12, 0.16]) + 0.035 * blob(p, [0, -0.23, 0.32], [0.17, 0.12, 0.15])             # chin, muzzle
    f += 0.030 * blob(p, [0, 0.06, -0.38], [0.24, 0.20, 0.13])                                                                   # back of skull
    # hair volume: a cap of hair above the hairline, thicker at the back
    hair = hair_mask(p)
    f += 0.06 * hair * (0.6 + 0.4 * sm((-p[..., 2] + 0.1) / 0.4))
    return r0 * (1.0 + f)

def hair_mask(p):
    """1 where there is hair (top and back), 0 on the face. The hairline is high at the front,
    drops past the temples and ends at the nape; a small wave at the front."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    th = np.arctan2(x, z)                                   # 0 = front, +-pi = back
    k = ((1 + np.cos(th)) / 2) ** 1.4
    front = sm((z + 0.02) / 0.3)
    wave = (0.02 * np.sin(x * 38.0) + 0.012 * np.cos(x * 61.0 + 1.3)) * front
    line = -0.10 + 0.36 * k + wave
    return np.clip(sm((y - line) / 0.03), 0, 1)

def concentrate(n, bands):
    fine = np.linspace(0, 1, 4096); dens = np.ones_like(fine)
    for lo, hi, s in bands:
        b = np.clip((fine - lo) / max(hi - lo, 1e-6), 0, 1)
        dens += (s - 1.0) * np.where((fine >= lo) & (fine <= hi), np.sin(np.pi * b) ** 2, 0.0)
    cum = np.cumsum(dens); cum -= cum[0]; cum /= cum[-1]
    return np.interp((np.arange(n) + 0.5) / n, cum, fine)

# ---------------- grid ----------------
GT, GP = 112, 68
u_col = concentrate(GT, [(0.28, 0.72, 3.4)])
u_col = np.concatenate([u_col, [u_col[0] + 1.0]])       # wrap column (duplicate seam)
GTW = GT + 1
v_row = concentrate(GP, [(0.36, 0.52, 1.9), (0.62, 0.82, 2.4)])
# make sure one row lands exactly on the mouth: find the row whose front point is nearest MOUTH_Y and nudge it
U, V = np.meshgrid(u_col, v_row)
D = sphere_dirs(U % 1.0, V)
R = head_radius(D)
P = D * R[..., None]
front_y = P[:, GT // 2, 1]
pm = int(np.argmin(np.abs(front_y - MOUTH_Y)))
# adjust that row's v so the front point sits on MOUTH_Y
for _ in range(6):
    v0 = v_row[pm]; d0 = sphere_dirs(np.array([0.5]), np.array([v0])); y0 = (d0 * head_radius(d0)[..., None])[0, 1]
    v1 = v0 + 0.002; d1 = sphere_dirs(np.array([0.5]), np.array([v1])); y1 = (d1 * head_radius(d1)[..., None])[0, 1]
    v_row[pm] = v0 + (MOUTH_Y - y0) * 0.002 / (y1 - y0)
U, V = np.meshgrid(u_col, v_row)
D = sphere_dirs(U % 1.0, V)
R = head_radius(D)
P = (D * R[..., None]).reshape(-1, 3)
UV = np.stack([U.ravel(), V.ravel()], 1)
vid = lambda p, t: p * GTW + t

# mouth slit columns on row pm: those with |x| < MOUTH_HW
row_x = P[[vid(pm, t) for t in range(GTW)], 0]; row_z = P[[vid(pm, t) for t in range(GTW)], 2]
slit = [t for t in range(GTW) if abs(row_x[t]) < MOUTH_HW and row_z[t] > 0]
assert slit == list(range(slit[0], slit[-1] + 1)), 'slit must be one run of columns'
t0, t1 = slit[0], slit[-1]
print('mouth row', pm, 'y=%.3f' % P[vid(pm, GT // 2), 1], 'slit columns', t0, t1, 'n', len(slit))

# duplicate interior slit vertices (corners t0 and t1 stay shared)
dup = {}
Pl = [P]; UVl = [UV]
extra = []
for t in range(t0 + 1, t1):
    dup[t] = len(P) + len(extra); extra.append(vid(pm, t))
P = np.vstack([P, P[extra]]); UV = np.vstack([UV, UV[extra]])
NV = len(P)
lower_copy = np.zeros(NV, bool); lower_copy[len(P) - len(extra):] = True
upper_cut = np.zeros(NV, bool)
for t in range(t0 + 1, t1): upper_cut[vid(pm, t)] = True

quads = []
for p in range(GP - 1):
    for t in range(GT):
        c = [(p, t), (p + 1, t), (p + 1, t + 1), (p, t + 1)]
        ids = []
        for (pp, tt) in c:
            i = vid(pp, tt)
            if p >= pm and pp == pm and tt in dup: i = dup[tt]      # quads below the cut use the lower copies
            ids.append(i)
        quads.append(ids)
quads = np.array(quads, np.int64)
# drop degenerate quads at the poles (top row / bottom row collapse to a point) -> triangles handle it
tris = np.vstack([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]])
# remove zero-area triangles
def area(T):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return np.linalg.norm(np.cross(b - a, c - a), axis=1)
tris = tris[area(tris) > 1e-9]
# orientation: make normals point outward (grid winding gives inward; flip if needed)
a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
fn = np.cross(b - a, c - a); cen = (a + b + c) / 3
if (fn * cen).sum() < 0: tris = tris[:, [0, 2, 1]]
print('verts', NV, 'tris', len(tris))

# ---------------- per-vertex data ----------------
x, y, z = P[:, 0], P[:, 1], P[:, 2]
# jaw weight: the whole lower lip and chin swing; fades to the cheeks and to the back
lat = 1 - sm((np.abs(x) - MOUTH_HW) / 0.10)
frontness = sm((z + 0.02) / 0.18)
below = sm((MOUTH_Y - y) / 0.012)
jaw = lat * frontness * below
jaw[lower_copy] = 1.0 * lat[lower_copy] * frontness[lower_copy]
jaw[upper_cut] = 0.0
# the row just above the cut must be 0; rows at the cut row outside the slit: taper
jaw[[vid(pm, t) for t in range(GTW) if not (t0 < t < t1)]] = 0.0
jaw = np.clip(jaw, 0, 1)

hw = hair_mask(P) * (0.35 + 0.65 * sm((-z + 0.15) / 0.35)) * (0.5 + 0.5 * sm((0.42 - y) / 0.25))
hw = np.clip(hw, 0, 1)

kind = np.zeros(NV)
for sx in (-1, 1):
    q = ((x - sx * EYE_X) / (EYE_A * 1.18)) ** 2 + ((y - EYE_Y) / (EYE_B * 1.6)) ** 2
    kind[(q < 1.0) & (z > 0.2)] = 1.0

# Surprise shape key (deltas): brows up, forehead up a little, cheeks up and out, nostrils flare,
# upper lip and teeth up, mouth corners in and down. Zero on the back of the head.
expr = np.zeros((NV, 3))
for sx in (-1, 1):
    bw = blob(P, [sx * EYE_X, BROW_Y, 0.34], [0.13, 0.05, 0.14])
    expr[:, 1] += 0.038 * bw; expr[:, 2] += 0.006 * bw
    fh = blob(P, [sx * EYE_X, BROW_Y + 0.12, 0.30], [0.16, 0.08, 0.16])
    expr[:, 1] += 0.016 * fh
    ck = blob(P, [sx * 0.20, -0.09, 0.28], [0.13, 0.11, 0.15])
    expr[:, 0] += sx * 0.012 * ck; expr[:, 1] += 0.016 * ck; expr[:, 2] += 0.008 * ck
    nw = blob(P, [sx * 0.06, NOSE_Y - 0.045, 0.36], [0.04, 0.035, 0.06])
    expr[:, 0] += sx * 0.012 * nw; expr[:, 1] += 0.006 * nw
    co = blob(P, [sx * MOUTH_HW, MOUTH_Y, 0.31], [0.05, 0.05, 0.08])
    expr[:, 0] -= sx * 0.028 * co; expr[:, 1] -= 0.018 * co
ul = blob(P, [0, MOUTH_Y + 0.03, 0.33], [0.09, 0.035, 0.10]) * (~lower_copy) * (y >= MOUTH_Y - 1e-6)
expr[:, 1] += 0.022 * ul; expr[:, 2] += 0.004 * ul
expr *= sm((z + 0.1) / 0.3)[:, None]

# ---------------- normals (welded by position so seam copies agree) ----------------
key = np.round(P, 5)
_, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
fn = np.cross(b - a, c - a)
acc = np.zeros((inv.max() + 1, 3))
for k in range(3): np.add.at(acc, inv[tris[:, k]], fn)
N = acc[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)

# ---------------- MouthOpen shape key (jaw rotated about the pivot) ----------------
PIVOT = np.array([0.0, MOUTH_Y, 0.07]); JAW_MAX = 0.30
def rotx(v, ang):
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([v[:, 0], v[:, 1] * c - v[:, 2] * s, v[:, 1] * s + v[:, 2] * c], 1)
mouth_open = rotx(P - PIVOT, JAW_MAX * jaw) + PIVOT - P

# ---------------- mouth interior (for Blender; the page draws its own) ----------------
CAV_C = np.array([0.0, MOUTH_Y - 0.01, 0.19]); CAV_R = np.array([MOUTH_HW + 0.01, 0.07, 0.075])
def ellipsoid(c, r, nu=20, nv=28):
    V_, Nn, T, J = [], [], [], []
    for i in range(nu + 1):
        th = np.pi * i / nu
        for j in range(nv + 1):
            ph = 2 * np.pi * j / nv
            d = np.array([np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)])
            V_.append(c + d * r); n = d / r; Nn.append(-n / np.linalg.norm(n))
            t = np.clip((0.15 - d[1]) / 0.5, 0, 1); J.append(t * t * (3 - 2 * t))
    for i in range(nu):
        for j in range(nv):
            a_ = i * (nv + 1) + j; b_ = a_ + nv + 1
            T += [[a_, a_ + 1, b_], [b_, a_ + 1, b_ + 1]]
    return np.array(V_), np.array(Nn), np.array(T, np.int64), np.array(J)
CV, CN, CT, CJ = ellipsoid(CAV_C, CAV_R)
cav_open = rotx(CV - PIVOT, JAW_MAX * CJ) + PIVOT - CV

# ---------------- texture (painted by evaluating the same 3D positions per texel) ----------------
TW = TH = 1024
tu = (np.arange(TW) + 0.5) / TW; tv = (np.arange(TH) + 0.5) / TH
TU, TV = np.meshgrid(tu, tv)
TD = sphere_dirs(TU, TV); TP = TD * head_radius(TD)[..., None]
tx, ty, tz = TP[..., 0], TP[..., 1], TP[..., 2]
skin = np.array([0.93, 0.74, 0.62])
img = np.ones((TH, TW, 3)) * skin
img *= 1.0 - 0.06 * sm((0.0 - tz) / 0.4)[..., None]                                 # a touch darker toward the back
blush = blob(TP, [-0.21, -0.11, 0.30], [0.12, 0.08, 0.14]) + blob(TP, [0.21, -0.11, 0.30], [0.12, 0.08, 0.14])
img = img * (1 - 0.35 * blush[..., None]) + np.array([0.98, 0.62, 0.58]) * 0.35 * blush[..., None]
# lips: a band above and below the cut
lipc = np.array([0.80, 0.40, 0.42])
upper_lip = sm((ty - (MOUTH_Y + 0.004)) / 0.006) * sm(((MOUTH_Y + 0.045) - ty) / 0.012) * sm((MOUTH_HW + 0.012 - np.abs(tx)) / 0.02) * sm((tz - 0.15) / 0.1)
lower_lip = sm(((MOUTH_Y - 0.004) - ty) / 0.006) * sm((ty - (MOUTH_Y - 0.048)) / 0.014) * sm((MOUTH_HW + 0.005 - np.abs(tx)) / 0.02) * sm((tz - 0.15) / 0.1)
lips = np.clip(upper_lip + lower_lip, 0, 1)
img = img * (1 - lips[..., None]) + lipc * lips[..., None]
# teeth: a thin white strip on the upper side right at the cut
teeth = sm((ty - MOUTH_Y) / 0.003) * sm(((MOUTH_Y + 0.014) - ty) / 0.004) * sm((MOUTH_HW - 0.01 - np.abs(tx)) / 0.02) * sm((tz - 0.15) / 0.1)
teeth_col = np.array([0.97, 0.96, 0.92])[None, None, :] * (1 - 0.18 * (np.abs(np.sin(tx * 180.0)) > 0.93))[..., None]   # faint tooth lines
img = img * (1 - teeth[..., None]) + teeth_col * teeth[..., None]
# brows
browc = np.array([0.34, 0.22, 0.14])
brow = 0
for sx in (-1, 1):
    arc_y = BROW_Y + 0.02 * np.cos((tx - sx * EYE_X) / 0.11 * np.pi / 2) - 0.012
    brow = brow + sm((0.012 - np.abs(ty - arc_y)) / 0.008) * sm((0.105 - np.abs(tx - sx * EYE_X)) / 0.03) * sm((tz - 0.2) / 0.1)
brow = np.clip(brow, 0, 1)
img = img * (1 - brow[..., None]) + browc * brow[..., None]
# nostrils
nos = blob(TP, [-0.045, NOSE_Y - 0.075, 0.37], [0.02, 0.012, 0.03]) + blob(TP, [0.045, NOSE_Y - 0.075, 0.37], [0.02, 0.012, 0.03])
img *= 1 - 0.55 * np.clip(nos, 0, 1)[..., None]
# hair
hairc = np.array([0.36, 0.22, 0.12])
hm = hair_mask(TP)
strands = 0.5 + 0.5 * np.sin(TU * 2 * np.pi * 90 + np.sin(TV * 40) * 2.0)
hair_col = hairc * (0.85 + 0.3 * strands)[..., None]
img = img * (1 - hm[..., None]) + hair_col * hm[..., None]
img8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
Image.fromarray(img8).save(os.path.join(OUT, 'basecolor.jpg'), quality=88)
jpg_bytes = open(os.path.join(OUT, 'basecolor.jpg'), 'rb').read()

# ---------------- GLB ----------------
def f32(a): return np.ascontiguousarray(a, np.float32).tobytes()
blobs = []; views = []; accs = []
def add_view(b, target=None):
    off = sum(len(x) for x in blobs); pad = (-len(b)) % 4
    blobs.append(b + b'\0' * pad)
    v = {"buffer": 0, "byteOffset": off, "byteLength": len(b)}
    if target: v["target"] = target
    views.append(v); return len(views) - 1
def add_acc(arr, typ, comp=5126, target=34962, minmax=False):
    arr = np.asarray(arr)
    b = f32(arr) if comp == 5126 else np.ascontiguousarray(arr, np.uint32 if comp == 5125 else np.uint16).tobytes()
    v = add_view(b, target)
    n = len(arr) if arr.ndim > 1 or typ == 'SCALAR' else len(arr)
    a = {"bufferView": v, "componentType": comp, "count": int(arr.shape[0]), "type": typ}
    if minmax: a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
    accs.append(a); return len(accs) - 1
ip = add_acc(P, 'VEC3', minmax=True); inn = add_acc(N, 'VEC3'); iuv = add_acc(UV, 'VEC2')
ij = add_acc(jaw, 'SCALAR'); ih = add_acc(hw, 'SCALAR'); ik = add_acc(kind, 'SCALAR')
imo = add_acc(mouth_open, 'VEC3', minmax=True); isu = add_acc(expr, 'VEC3', minmax=True)
ctype = 5123 if NV <= 65535 else 5125
iidx = add_acc(tris.ravel(), 'SCALAR', comp=ctype, target=34963)
cp = add_acc(CV, 'VEC3', minmax=True); cn = add_acc(CN, 'VEC3'); cmo = add_acc(cav_open, 'VEC3', minmax=True)
czero = add_acc(np.zeros_like(CV), 'VEC3', minmax=True)
cidx = add_acc(CT.ravel(), 'SCALAR', comp=5123, target=34963)
iimg = add_view(jpg_bytes)
gltf = {
  "asset": {"version": "2.0", "generator": "stretchy-head-template gen_head.py"},
  "scene": 0, "scenes": [{"nodes": [0, 1]}],
  "nodes": [{"name": "Head", "mesh": 0}, {"name": "MouthInterior", "mesh": 1}],
  "meshes": [
    {"name": "Head", "primitives": [{"attributes": {"POSITION": ip, "NORMAL": inn, "TEXCOORD_0": iuv, "_JAW_WEIGHT": ij, "_HAIR_WEIGHT": ih, "_EYE_PART": ik},
                                     "indices": iidx, "material": 0, "targets": [{"POSITION": imo}, {"POSITION": isu}]}],
     "extras": {"targetNames": ["MouthOpen", "Surprise"]}},
    {"name": "MouthInterior", "primitives": [{"attributes": {"POSITION": cp, "NORMAL": cn}, "indices": cidx, "material": 1,
                                              "targets": [{"POSITION": cmo}, {"POSITION": czero}]}],
     "extras": {"targetNames": ["MouthOpen", "Surprise"]}}],
  "materials": [{"name": "HeadPaint", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0, "roughnessFactor": 0.7}},
                {"name": "MouthInterior", "pbrMetallicRoughness": {"baseColorFactor": [0.3, 0.06, 0.07, 1], "metallicFactor": 0, "roughnessFactor": 0.8}, "doubleSided": True}],
  "textures": [{"source": 0}], "images": [{"bufferView": iimg, "mimeType": "image/jpeg", "name": "basecolor"}],
  "bufferViews": views, "accessors": accs, "buffers": [{"byteLength": sum(len(b) for b in blobs)}]
}
jb = json.dumps(gltf, separators=(',', ':')).encode(); jb += b' ' * ((-len(jb)) % 4)
bb = b''.join(blobs)
glb = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(jb) + 8 + len(bb)) + struct.pack('<II', len(jb), 0x4E4F534A) + jb + struct.pack('<II', len(bb), 0x004E4942) + bb
open(os.path.join(OUT, 'head.glb'), 'wb').write(glb)

# eye ellipse centres on the surface
def surf(xy):
    d = np.array([xy[0], xy[1], 0.45]); d = d / np.linalg.norm(d)
    return (d * head_radius(d[None, :])[0]).tolist()
eyes = [{"c": surf([-EYE_X, EYE_Y]), "a": EYE_A, "b": EYE_B, "th": 0.0}, {"c": surf([EYE_X, EYE_Y]), "a": EYE_A, "b": EYE_B, "th": 0.0}]
H = {
  "_about": "Numbers the Stretchy Head page needs for this head. Head space: about 1 unit tall, centred at the origin, +y up, +z toward the viewer. See ASSET-SPEC.md.",
  "mirrorX": 0.0,
  "pivot": PIVOT.tolist(), "jawMax": JAW_MAX,
  "cav": {"c": CAV_C.tolist(), "r": CAV_R.tolist()},
  "eyes": eyes, "irisScale": 0.86,
  "skin": skin.tolist(),
  "eyeLine": [EYE_Y - 0.03, EYE_Y + 0.01],
  "mouthCorner": [MOUTH_HW - 0.035, MOUTH_HW],
  "cheek": [MOUTH_HW + 0.07, MOUTH_Y + 0.09]
}
json.dump(H, open(os.path.join(OUT, 'head.json'), 'w'), indent=1)
print('wrote', len(glb), 'bytes; jaw>0.5:', int((jaw > 0.5).sum()), 'hair>0:', int((hw > 0.01).sum()), 'eye verts:', int(kind.sum()))
