# wendys-2
Simple 3D rendering engine using raytracing.

Supports colors, reflectivity, view-angle simulated darkness, colors, skylight, axis aligned cuboids and arbitrary triangles.

## Example usage:
```python
world = World()
mainCam = Camera((posx, posy, posz), fov, width, height, pitch, yaw)
box = AlignedCuboid((posx, posy, posz), Color(r, g, b), isMirror = False, reflectiveness = 50, darkiness = 50)
tri = Triangle((v1x, v1y, v1z), (v2x, v2y, v2z), (v3x, v3y, v3z), Color(r, g, b), isMirror = True, reflectiveness = 100, darkiness = 0)
world.add(box, tri)


```
