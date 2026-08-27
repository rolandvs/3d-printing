#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parametrisch model van het witte kunststof beugeltje (IKEA TILLREDA / TALLBODA deurbeslag).
Alle maten in mm. Pas het PARAMETERS-blok aan en run opnieuw -> nieuwe STL's.

Opbouw:
  - grondplaat: unie van 2 oorcirkels (schroefgaten) + 1 grote lob, met filet in de taille
  - op de lob: ronde hals + rechthoekige (afgeronde) kop  -> "T"/paddenstoel
  - centraal gat door alles heen, verzonken vanaf de bovenkant
  - beide oorgaten verzonken vanaf de bovenkant van de plaat
"""
import math
import numpy as np

# ----------------------------- PARAMETERS -----------------------------------
# Alles gemeten uit de rechtstreekse bovenaanzicht-foto (silhouet), geschaald op
# h.o.h. = 27 mm. Oorsprong = hart centraal gat; +y = ronde kant; x = langs de
# rechte onderrand. LET OP: de twee oren staan versprongen (niet op een lijn
# loodrecht op de kop-as) - dat is de vorm van het origineel.
EAR_L_XY     = (-13.50, -0.46)   # hart schroefgat links   (gemeten)
EAR_R_XY     = ( 13.15, -4.77)   # hart schroefgat rechts  (gemeten, h.o.h. 27,0)
R_EAR        = 5.80              # oor D11,6               (cirkelfit, rms 0,2)
D_SCREW      = 4.0               # schroefgaten
D_CS_EAR     = 6.5               # verzinking oorgat
D_SCREW_MID  = 4.0               # centraal gat
D_CS_MID     = 6.0               # verzinking centraal gat

PLATE_R      = 11.15             # grote ronde lob, concentrisch met het middengat
                                 # (cirkelfit op de bovenrand, rms 0,01 mm)
PLATE_FLAT   = 7.90              # rechte onderrand, onder het middengat
K_FILLET     = 2.0               # filet waar oor en lob samenkomen

HEAD_CY      = 2.50              # hart van de ronde kant van kop/hals boven C
HEAD_W       = 14.0              # kop breedte             (GEMETEN met schuifmaat)
HEAD_R       = 7.0               # kop ronde kant (= HEAD_W/2), top op +9,5
HEAD_FLAT    = 6.40              # HEAD_CY -> rechte kant  (= 4 mm binnen de plaatrand)
R_NECK       = 4.0               # hals D8, rechte kant vlak met de kop

T_PLATE      = 3.0
H_NECK       = 3.0
H_HEAD       = 3.0

N_OUT        = 200    # segmenten buitencontour
N_HOLE       = 64     # segmenten per rond element (gaten, hals)
N_HEAD       = 64     # segmenten kop-contour (moet gelijk zijn aan N_HOLE)
# -----------------------------------------------------------------------------

R_SCREW = D_SCREW / 2.0
R_SCREW_MID = D_SCREW_MID / 2.0
C = np.array([0.0, 0.0])                 # hart centraal gat
D_C = np.array([0.0, HEAD_CY])           # hart van de ronde kant van kop en hals
EAR_L = np.array(EAR_L_XY)
EAR_R = np.array(EAR_R_XY)

Z0 = 0.0
Z1 = T_PLATE
Z2 = T_PLATE + H_NECK
Z3 = T_PLATE + H_NECK + H_HEAD

CS_EAR_DEPTH = (D_CS_EAR - D_SCREW) / 2.0
CS_MID_DEPTH = (D_CS_MID - D_SCREW_MID) / 2.0


# ----------------------- 2D helpers: SDF + radiale sampling ------------------
def sdf_circle(p, c, r):
    return np.hypot(p[0] - c[0], p[1] - c[1]) - r


def smin(a, b, k):
    """kwadratische smooth-min -> exacte filet met straal ~k in de holle hoek"""
    if k <= 0:
        return min(a, b)
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def _sdf_D(p, center, r, flat, half_w):
    """halfronde kop: halve cirkel (radius r) + recht stuk tot `flat` onder het hart"""
    x = abs(p[0] - center[0])
    y = p[1] - center[1]
    if y >= 0:                              # ronde helft
        d = math.hypot(x, y) - r
    else:                                   # rechte helft (rechthoek)
        dx = x - half_w
        dy = -y - flat
        d = min(max(dx, dy), 0.0) + math.hypot(max(dx, 0.0), max(dy, 0.0))
    return d


def sdf_plate(p):
    """twee oorcirkels + grote lob, waarbij alleen de lob recht wordt afgesneden"""
    a = sdf_circle(p, EAR_L, R_EAR)
    b = sdf_circle(p, EAR_R, R_EAR)
    lobe = max(sdf_circle(p, C, PLATE_R), -PLATE_FLAT - p[1])
    return smin(smin(a, b, 0.0), lobe, K_FILLET)


def sdf_head(p):
    return _sdf_D(p, D_C, HEAD_R, HEAD_FLAT, HEAD_W / 2.0)


def sdf_neck(p):
    return _sdf_D(p, D_C, R_NECK, HEAD_FLAT, R_NECK)


def radial_contour(sdf, center, n, rmax=40.0, step=0.05):
    """convexe/stervormige contour per hoek rond `center` (buitenste overgang)"""
    center = np.asarray(center, dtype=float)
    assert sdf(center) < 0, "centrum ligt niet in het materiaal"
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        d = np.array([math.cos(th), math.sin(th)])
        r = rmax
        while r > 0 and sdf(center + d * r) >= 0:
            r -= step
        lo, hi = r, r + step
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if sdf(center + d * mid) < 0:
                lo = mid
            else:
                hi = mid
        pts.append(center + d * (0.5 * (lo + hi)))
    return np.array(pts)


def trace_contour(sdf, inside_pt, ds=0.3, h=1e-4, max_steps=20000):
    """volgt de nullijn van `sdf` rondom (predictor-corrector). Werkt ook bij
    holle stukken (taille), in tegenstelling tot radiaal aftasten."""
    p = np.asarray(inside_pt, dtype=float).copy()
    assert sdf(p) < 0
    # startpunt op de rand zoeken (recht omhoog)
    lo, hi = 0.0, 40.0
    while sdf(p + np.array([0.0, hi])) < 0:
        hi *= 2
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if sdf(p + np.array([0.0, mid])) < 0:
            lo = mid
        else:
            hi = mid
    start = p + np.array([0.0, 0.5 * (lo + hi)])

    def grad(q):
        gx = (sdf((q[0] + h, q[1])) - sdf((q[0] - h, q[1]))) / (2 * h)
        gy = (sdf((q[0], q[1] + h)) - sdf((q[0], q[1] - h))) / (2 * h)
        g = np.array([gx, gy])
        n = np.linalg.norm(g)
        return g / n if n > 1e-12 else np.array([0.0, 1.0])

    pts = [start.copy()]
    q = start.copy()
    for step in range(max_steps):
        n = grad(q)
        t = np.array([-n[1], n[0]])          # CCW langs de rand
        q = q + t * ds
        for _ in range(4):                   # terugprojecteren op de rand
            n2 = grad(q)
            q = q - n2 * sdf(q)
        if step > 10 and np.hypot(*(q - start)) < ds * 0.9:
            break
        pts.append(q.copy())
    else:
        raise RuntimeError("contour sluit niet")
    return np.array(pts)


def drop_collinear(poly, tol=1e-7):
    """verwijder punten die op een rechte tussen hun buren liggen (voorkomt
    T-splitsingen tussen wand en dekvlak)"""
    p = list(poly)
    out = []
    n = len(p)
    for i in range(n):
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        cr = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if abs(cr) > tol:
            out.append(b)
    return np.array(out)


def circle_pts(c, r, n, ccw=True):
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    if not ccw:
        th = -th
    return np.stack([c[0] + r * np.cos(th), c[1] + r * np.sin(th)], axis=1)


def poly_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


# --------------------------- triangulatie met gaten --------------------------
def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _proper_cross(p1, p2, p3, p4):
    """echte kruising van twee segmenten (gedeelde eindpunten tellen niet mee)"""
    for a in (p1, p2):
        for b in (p3, p4):
            if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
                return False
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y):
            xi = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if xi > x:
                inside = not inside
    return inside


def eliminate_holes(outer, holes):
    """verbind elk gat met de buitenlus via een brug naar het dichtstbijzijnde
    zichtbare punt -> een simpele polygoon. Zichtbaarheid wordt expliciet
    getest, dus geen aannames over ligging of orientatie."""
    outer = [np.asarray(p, dtype=float) for p in outer]
    holes = sorted(holes, key=lambda h: -max(p[0] for p in h))
    for hole in holes:
        hole = [np.asarray(p, dtype=float) for p in hole]
        edges = [(outer[i], outer[(i + 1) % len(outer)]) for i in range(len(outer))]
        edges += [(hole[i], hole[(i + 1) % len(hole)]) for i in range(len(hole))]
        done = False
        # probeer elk gatpunt (meestal slaagt het eerste al)
        for m_idx in range(len(hole)):
            M = hole[m_idx]
            order = sorted(range(len(outer)), key=lambda i: np.hypot(*(outer[i] - M)))
            for p_idx in order:
                P = outer[p_idx]
                if any(_proper_cross(M, P, a, b) for (a, b) in edges):
                    continue
                mid = (M + P) / 2.0
                if not _point_in_poly(mid, outer):
                    continue
                if any(_point_in_poly(mid, h) for h in [hole]):
                    continue
                rot = hole[m_idx:] + hole[:m_idx]
                outer = outer[:p_idx + 1] + rot + [rot[0]] + outer[p_idx:]
                done = True
                break
            if done:
                break
        if not done:
            raise RuntimeError("geen geldige brug gevonden voor gat")
    return np.array(outer)


def triangulate(poly):
    """ear-clipping op een simpele CCW-polygoon"""
    pts = np.asarray(poly, dtype=float)
    idx = list(range(len(pts)))
    if poly_area(pts) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3:
        guard += 1
        if guard > 20000:
            raise RuntimeError("ear-clipping vastgelopen")
        made = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            cr = _cross(a, b, c)
            if cr <= 1e-12:                      # reflex of ontaard
                if abs(cr) <= 1e-12:             # ontaard: uitgeven en knippen
                    tris.append((i0, i1, i2))
                    idx.pop(k)
                    made = True
                    break
                continue
            others = [j for j in idx if j not in (i0, i1, i2)]
            if others:
                q = pts[others]
                d0 = (b[0]-a[0])*(q[:,1]-a[1]) - (b[1]-a[1])*(q[:,0]-a[0])
                d1 = (c[0]-b[0])*(q[:,1]-b[1]) - (c[1]-b[1])*(q[:,0]-b[0])
                d2 = (a[0]-c[0])*(q[:,1]-c[1]) - (a[1]-c[1])*(q[:,0]-c[0])
                if np.any((d0 > 1e-12) & (d1 > 1e-12) & (d2 > 1e-12)):
                    continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            made = True
            break
        if not made:
            raise RuntimeError("geen oor gevonden")
    tris.append((idx[0], idx[1], idx[2]))
    return pts, tris


# ------------------------------- mesh-opbouw ---------------------------------
class Mesh:
    def __init__(self):
        self.v = []
        self.f = []

    def add(self, p):
        self.v.append(np.asarray(p, dtype=float))
        return len(self.v) - 1

    def ring(self, pts2d, z):
        return [self.add((p[0], p[1], z)) for p in pts2d]

    def tri(self, a, b, c):
        self.f.append((a, b, c))

    def quad(self, a, b, c, d):
        self.tri(a, b, c)
        self.tri(a, c, d)

    def wall(self, ring_lo, ring_hi, outward=True):
        """gesloten zijwand tussen twee gelijk-gesampelde ringen (CCW van boven)"""
        n = len(ring_lo)
        for i in range(n):
            j = (i + 1) % n
            if outward:
                self.quad(ring_lo[i], ring_lo[j], ring_hi[j], ring_hi[i])
            else:
                self.quad(ring_lo[i], ring_hi[i], ring_hi[j], ring_lo[j])

    def cap(self, outer2d, holes2d, z, up=True):
        # kleine rotatie voorkomt ontaarde gevallen (assen-parallelle raaklijnen)
        th = 0.4137
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        rot = lambda a: np.asarray(a) @ R.T
        poly = eliminate_holes([tuple(p) for p in rot(outer2d)],
                               [[tuple(p) for p in rot(h)] for h in holes2d])
        pts, tris = triangulate(poly)
        pts = pts @ R          # terugdraaien (R^-1 = R^T, dus pts @ R)
        # hergebruik bestaande ring-indices niet: cap krijgt eigen vertices
        base = [self.add((p[0], p[1], z)) for p in pts]
        for (a, b, c) in tris:
            if up:
                self.tri(base[a], base[b], base[c])
            else:
                self.tri(base[a], base[c], base[b])
        return pts, tris

    def _tri_ok(self, a, b, c):
        p, q, r = self.v[a], self.v[b], self.v[c]
        return abs(np.cross(q - p, r - p)).sum() > 1e-9

    def strip(self, inner2d, outer2d, z, up=True):
        """vlakke ring tussen twee gelijk-gesampelde, concentrische contouren"""
        ri = self.ring(inner2d, z)
        ro = self.ring(outer2d, z)
        n = len(ri)
        for i in range(n):
            j = (i + 1) % n
            q = (ri[i], ro[i], ro[j], ri[j]) if up else (ri[i], ri[j], ro[j], ro[i])
            for t in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                if self._tri_ok(*t):
                    self.tri(*t)
        return ri, ro


def build():
    m = Mesh()

    # --- 2D contouren -------------------------------------------------------
    outer = drop_collinear(trace_contour(sdf_plate, C))
    head = radial_contour(sdf_head, D_C, N_HEAD)
    assert N_HEAD == N_HOLE

    hole_l_lo = circle_pts(EAR_L, R_SCREW, N_HOLE, ccw=False)   # CW = gat
    hole_r_lo = circle_pts(EAR_R, R_SCREW, N_HOLE, ccw=False)
    hole_m_lo = circle_pts(C, R_SCREW_MID, N_HOLE, ccw=False)
    hole_l_hi = circle_pts(EAR_L, D_CS_EAR / 2.0, N_HOLE, ccw=False)
    hole_r_hi = circle_pts(EAR_R, D_CS_EAR / 2.0, N_HOLE, ccw=False)
    neck = radial_contour(sdf_neck, D_C, N_HOLE)
    neck_cw = neck[::-1]

    # --- onderkant plaat (normaal -Z) --------------------------------------
    m.cap(outer, [hole_l_lo, hole_r_lo, hole_m_lo], Z0, up=False)
    # --- bovenkant plaat (normaal +Z): oorverzinkingen + halsvoetafdruk -----
    m.cap(outer, [hole_l_hi, hole_r_hi, neck_cw], Z1, up=True)

    # --- buitenwand plaat ---------------------------------------------------
    r_lo = m.ring(outer, Z0)
    r_hi = m.ring(outer, Z1)
    m.wall(r_lo, r_hi, outward=True)

    # --- oorgaten: cilinder + conische verzinking ---------------------------
    for c0 in (EAR_L, EAR_R):
        z_cs = Z1 - CS_EAR_DEPTH
        a = m.ring(circle_pts(c0, R_SCREW, N_HOLE), Z0)
        b = m.ring(circle_pts(c0, R_SCREW, N_HOLE), z_cs)
        c = m.ring(circle_pts(c0, D_CS_EAR / 2.0, N_HOLE), Z1)
        m.wall(a, b, outward=False)
        m.wall(b, c, outward=False)

    # --- hals ---------------------------------------------------------------
    n_lo = m.ring(neck, Z1)
    n_hi = m.ring(neck, Z2)
    m.wall(n_lo, n_hi, outward=True)

    # --- onderkant kop (overhang-ring, normaal -Z) --------------------------
    head_n = head
    m.strip(neck, head_n, Z2, up=False)

    # --- wand kop -----------------------------------------------------------
    h_lo = m.ring(head, Z2)
    h_hi = m.ring(head, Z3)
    m.wall(h_lo, h_hi, outward=True)

    # --- bovenkant kop: ring tussen verzinking en koprand -------------------
    head_n2 = head
    m.strip(circle_pts(C, D_CS_MID / 2.0, N_HOLE), head_n2, Z3, up=True)

    # --- centraal gat: cilinder Z0..(Z3-verzinking) + conus -----------------
    z_cs = Z3 - CS_MID_DEPTH
    a = m.ring(circle_pts(C, R_SCREW_MID, N_HOLE), Z0)
    b = m.ring(circle_pts(C, R_SCREW_MID, N_HOLE), z_cs)
    c = m.ring(circle_pts(C, D_CS_MID / 2.0, N_HOLE), Z3)
    m.wall(a, b, outward=False)
    m.wall(b, c, outward=False)

    return m


def drop_degenerate(m, tol=1e-9):
    """verwijder nul-oppervlak driehoeken; alleen als de mesh dicht blijft"""
    V = np.array(m.v)
    keep = []
    for (a, b, c) in m.f:
        ar = np.linalg.norm(np.cross(V[b] - V[a], V[c] - V[a])) / 2.0
        if ar > tol:
            keep.append((a, b, c))
    m.f = keep
    return m


# --------------------------------- controle ----------------------------------
def check(m, name=""):
    V = np.array(m.v)
    F = np.array(m.f, dtype=int)
    # samenvoegen van dubbele vertices voor de topologiecheck
    key = np.round(V, 5)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    G = inv[F]
    edges = {}
    for t in G:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges[(a, b)] = edges.get((a, b), 0) + 1
    bad_dir = sum(1 for e, n in edges.items() if n != 1)
    open_e = sum(1 for (a, b) in edges if (b, a) not in edges)
    p0, p1, p2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = np.sum(np.einsum('ij,ij->i', p0, np.cross(p1, p2))) / 6.0
    print(f"[{name}] driehoeken={len(F)}  vertices={len(np.unique(inv))}")
    print(f"[{name}] randen dubbel-in-zelfde-richting={bad_dir}  open randen={open_e}")
    print(f"[{name}] volume={vol:.3f} mm^3   bbox={V.min(0).round(2)} .. {V.max(0).round(2)}")
    return bad_dir == 0 and open_e == 0 and vol > 0


def write_stl(m, path, mirror=False):
    V = np.array(m.v)
    F = np.array(m.f, dtype=int)
    if mirror:
        V = V.copy()
        V[:, 0] *= -1
        F = F[:, ::-1]
    tri = V[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, np.where(ln == 0, 1, ln))
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(np.uint32(len(F)).tobytes())
        buf = bytearray()
        for i in range(len(F)):
            buf += np.array([n[i], tri[i, 0], tri[i, 1], tri[i, 2]], dtype="<f4").tobytes()
            buf += b"\0\0"
        f.write(bytes(buf))
    return path


if __name__ == "__main__":
    mesh = build()   # let op: 1 nul-oppervlak driehoek is nodig voor de topologie
    ok = check(mesh, "bracket")
    print("waterdicht + consistent:", ok)
    write_stl(mesh, "/mnt/user-data/outputs/tillreda_bracket_A.stl")
    write_stl(mesh, "/mnt/user-data/outputs/tillreda_bracket_B_gespiegeld.stl", mirror=True)
    print("STL's geschreven")
