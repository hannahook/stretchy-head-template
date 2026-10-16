# Asset spec: what `head.glb` and `head.json` must contain

The page (`index.html`) loads two files from its own folder. This is the contract. The included placeholder head follows it exactly, and `tools/gen_head.py` shows how it was produced.

## Coordinate space

- Head about **1 unit tall**, centred on the origin, **+y up, +z toward the viewer**. (The placeholder spans y ≈ −0.48 to 0.49.)
- The camera sits at z = 1.85 by default (`CFG.camZ` in `index.html`). A head much larger or smaller than 1 unit will look wrong; scale it before export.
- The symmetry plane is at `x = mirrorX` (see `head.json`). It is 0 for the placeholder.

## `head.glb`

A standard glTF 2.0 binary. Only the mesh named **`Head`** is used by the page; a second mesh (`MouthInterior`) may be included for the benefit of Blender but the page draws its own mouth interior.

`Head` must be one primitive, triangles, with these vertex attributes:

| Attribute | Type | Meaning |
| --- | --- | --- |
| `POSITION` | VEC3 float | rest position |
| `NORMAL` | VEC3 float | rest normal |
| `TEXCOORD_0` | VEC2 float | texture coordinates |
| `_JAW_WEIGHT` | SCALAR float 0–1 | how much the point follows the jaw when the mouth opens. **The mouth must be cut as a slit**: the vertices along the lip line exist twice, once for the upper lip (weight 0) and once for the lower lip (weight 1). Everything on the chin side of the cut carries a weight that fades to 0 toward the cheeks and the back. |
| `_HAIR_WEIGHT` | SCALAR float 0–1 | how much the point flops with the hair spring (0 for skin and the scalp roots, larger toward the hair tips) |
| `_EYE_PART` | SCALAR float | `0` skin · `1` eyeball surface (the page paints eyes over it) · `2` lash or lid strip geometry that the page should hide |

and these morph targets, named in `extras.targetNames` on the mesh:

| Target | Used by the page? | Meaning |
| --- | --- | --- |
| `MouthOpen` | no (Blender only) | every point rotated about the jaw pivot by `jawMax × _JAW_WEIGHT` |
| `Surprise` | **yes** | the exaggerated "surprised at being stretched" face: brows and forehead up, cheeks up and out, nostrils flared, upper lip and top teeth up, mouth corners in and down. Zero on the back of the head. The page splits this one shape into brows / mouth-centre / mouth-corners regions to make every other face. |

Indices may be 16- or 32-bit. The texture is the material's `baseColorTexture`; it may be embedded in the GLB or referenced by a relative URI. If the GLB has no texture, the page loads `basecolor.jpg` from the same folder.

The texture should contain **no painted eyes** (the page draws them) and should show the **top teeth painted along the upper side of the mouth cut**, because the page's mouth opening reveals that edge.

## `head.json`

```json
{
  "mirrorX": 0.0,
  "pivot": [0.0, -0.19, 0.07],
  "jawMax": 0.30,
  "cav": {"c": [0.0, -0.20, 0.19], "r": [0.125, 0.07, 0.075]},
  "eyes": [
    {"c": [-0.14, 0.05, 0.37], "a": 0.074, "b": 0.05, "th": 0.0},
    {"c": [ 0.14, 0.05, 0.37], "a": 0.074, "b": 0.05, "th": 0.0}
  ],
  "irisScale": 0.86,
  "skin": [0.93, 0.74, 0.62],
  "eyeLine": [0.02, 0.06],
  "mouthCorner": [0.08, 0.115],
  "cheek": [0.185, -0.10]
}
```

| Key | Meaning |
| --- | --- |
| `mirrorX` | x of the symmetry plane |
| `pivot` | the jaw hinge, in head space: on the mirror plane, at the height of the mouth cut, a little behind the lips |
| `jawMax` | full jaw opening in radians (informational; the page uses its own `CFG.jawMax`) |
| `cav` | the inner-mouth ellipsoid the page draws behind the teeth: centre `c` and radii `r`. Make it a little wider than the slit and deep enough that a wide-open mouth never shows the back wall |
| `eyes` | two eye openings: centre `c` on the face surface (rest space), semi-axes `a` (across) and `b` (up), tilt `th` in radians. Left eye first (negative x) |
| `irisScale` | iris radius as a fraction of `b` |
| `skin` | the skin colour (0–1 RGB) used where the drawn eyelid covers the eye |
| `eyeLine` | y range over which the Surprise shape switches from "mouth" control to "brow" control (just under the eyes to just above) |
| `mouthCorner` | \|x\| range over which the Surprise shape switches from "mouth centre" to "mouth corner" control (from inside the slit to its ends) |
| `cheek` | x, y of the spot the ghost demo pinches |

## How to produce these for a generated head

Hand Claude the GLB from your generator and ask for, in this order, each as its own build you approve: inspect; cut the mouth **along the mesh's existing edge loop** at the lip line (not along the painted lips) and add the inner mouth; flag the eye region and remove painted eyes from the texture; compute jaw, hair and eye weights; compute the Surprise shape; write `head.json`. Then open the page and check rest, mouth open, mid-blink, side and below before accepting it. See README.md for the full process.
