import numpy as np
import pygame, math, random, time
from numba import njit



"""
Axis directions
    Y
    ^
    |
    |                Z
    |              7
    |           /
    |        / 
    |     /
    |  /
    --------------------> X

"""






class Plane:
    def __init__(self, p1, p2, p3, p4, color:np.ndarray = np.array([255, 255, 255]), reflectiveness:float = 0):
        """
        Points must go around the plane
        :param p1: Point 1 of plane
        :param p2: Point 2 of plane
        :param p3: Point 3 of plane
        :param p4: Point 4 of plane
        :param color: Color of plane
        :param reflectiveness: Between 0 and 1. 0 means it will always return the base color, 1 means it will return the full reflected color (after filtering)
        """
        id1 = random.random()
        id2 = random.random()
        self.t1 = Triangle(np.array(p1), np.array(p2), np.array(p4), color=color, reflectiveness=reflectiveness, siblings = [id2], id=id1)
        self.t2 = Triangle(np.array(p2), np.array(p3), np.array(p4), color=color, reflectiveness=reflectiveness, siblings = [id1], id=id2)
    def add(self):
        world.append(self.t1)
        world.append(self.t2)



@njit(fastmath=True, cache=True)
def njit_rayIntersects(normal, D, p1, p2, p3, vec21, vec32, vec13, ray, origin):
    """
    :param ray: Normalised ray direction vector
    :param origin: Ray origin
    :param getReflected: If true, return reflected ray
    :return: (False, 0, 0, 0) if no hit,
    else:
    returns (True, hitpoint, travelDist, 0) if not getReflected
    returns (True, hitpoint, travelDist, reflectedDirection) if getReflected
    """
    if np.dot(ray, normal) == 0:
        return False, np.zeros(3, dtype=np.float64), 0, np.zeros(3, dtype=np.float64)
    t = -(np.dot(normal, origin) + D) / np.dot(normal, ray)
    if t < 0:
        return False, np.zeros(3, dtype=np.float64), 0, np.zeros(3, dtype=np.float64)
    hitPoint = origin + t * ray
    # left right checks
    if np.dot(normal, np.cross(hitPoint - p1, vec21)) < 0:
        return False, np.zeros(3, dtype=np.float64), 0, np.zeros(3, dtype=np.float64)
    if np.dot(normal, np.cross(hitPoint - p2, vec32)) < 0:
        return False, np.zeros(3, dtype=np.float64), 0, np.zeros(3, dtype=np.float64)
    if np.dot(normal, np.cross(hitPoint - p3, vec13)) < 0:
        return False, np.zeros(3, dtype=np.float64), 0, np.zeros(3, dtype=np.float64)
    # ray has hit
    reflected = ray - 2 * (np.dot(ray, normal) * normal)
    return True, hitPoint, t, reflected



class Triangle:
    def __init__(self, p1:np.ndarray, p2:np.ndarray, p3:np.ndarray, color:np.ndarray = np.array([255, 255, 255]), reflectiveness:float = 0, siblings = None, id = -1):
        """
        :param p1: Point 1 of triangle
        :param p2: Point 2 of triangle
        :param p3: Point 3 of triangle
        :param color: Color of triangle surface
        :param reflectiveness: Between 0 and 1. 0 means it will always return the base color, 1 means it will return the full reflected color (after filtering)
        """
        if id == -1:
            self.id = random.random()
        else:
            self.id = id
        self.p1 = p1.astype(float)
        self.p2 = p2.astype(float)
        self.p3 = p3.astype(float)

        self.vec12 = self.p2 - self.p1
        self.vec13 = self.p3 - self.p1
        self.vec23 = self.p3 - self.p2
        self.vec21 = -self.vec12
        self.vec31 = -self.vec13
        self.vec32 = -self.vec23

        self.normal = np.cross(self.vec12, self.vec13)
        self.normal = self.normal / np.linalg.norm(self.normal)
        self.D = -np.dot(self.normal, self.p1) # Ax + By + Cz + D = 0

        self.reflectiveness = reflectiveness
        self.color = color
        self.siblings = siblings


    def rayIntersects(self, ray, origin):
        """
        :param ray: Normalised ray direction vector
        :param origin: Ray origin
        :param getReflected: If true, return reflected ray
        :return: (False, 0, 0, 0) if no hit,
        else:
        returns (True, hitpoint, travelDist, 0) if not getReflected
        returns (True, hitpoint, travelDist, reflectedDirection) if getReflected
        """
        return njit_rayIntersects(self.normal, self.D, self.p1, self.p2, self.p3, self.vec21, self.vec32, self.vec13, ray, origin)
        # if np.dot(ray, self.normal) == 0:
        #     return False, 0, 0, 0
        # t = -(np.dot(self.normal, origin) + self.D) / np.dot(self.normal, ray)
        # if t < 0:
        #     return False, 0, 0, 0
        # hitPoint = origin + t * ray
        # # left right checks
        # if np.dot(self.normal, np.cross(hitPoint - self.p1, self.vec21)) < 0:
        #     return False, 0, 0, 0
        # if np.dot(self.normal, np.cross(hitPoint - self.p2, self.vec32)) < 0:
        #     return False, 0, 0, 0
        # if np.dot(self.normal, np.cross(hitPoint - self.p3, self.vec13)) < 0:
        #     return False, 0, 0, 0
        # # ray has hit
        # reflected = ray - 2 * (np.dot(ray, self.normal) * self.normal)
        # return True, hitPoint, t, reflected

    def add(self):
        world.append(self)


@njit(fastmath=True, cache=True)
def rotX(vec:np.ndarray, s: float, c: float):
    # rotMat = np.array([[c, -s, 0],
    #                    [s, c, 0],
    #                    [0, 0, 1]])
    rotMat = np.empty((3, 3))
    rotMat[0, 0] = c
    rotMat[0, 1] = -s
    rotMat[0, 2] = 0.0
    rotMat[1, 0] = s
    rotMat[1, 1] = c
    rotMat[1, 2] = 0.0
    rotMat[2, 0] = 0.0
    rotMat[2, 1] = 0.0
    rotMat[2, 2] = 1.0
    return np.dot(rotMat, vec)
    # return rotMat @ vec
@njit(fastmath=True, cache=True)
def rotY(vec:np.ndarray, s: float, c: float):
    # rotMat = np.array([[c, 0, s],
    #                    [0, 1, 0],
    #                    [-s, 0, c]])
    rotMat = np.empty((3, 3))
    rotMat[0, 0] = c
    rotMat[0, 1] = 0.0
    rotMat[0, 2] = s
    rotMat[1, 0] = 0.0
    rotMat[1, 1] = 1.0
    rotMat[1, 2] = 0.0
    rotMat[2, 0] = -s
    rotMat[2, 1] = 0.0
    rotMat[2, 2] = c
    return np.dot(rotMat, vec)
    # return rotMat @ vec

def normaliseVec(vec:np.ndarray):
    return vec / np.linalg.norm(vec)



class Camera:
    def __init__(self, pos:np.ndarray, resolution, fov:float = 110, pitch:float = 0, yaw:float = 0):
        """
        Points in positive Z direction by default
        :param pos: Camera origin
        :param resolution: Resolution of camera (width, height)
        :param fov: FOV of camera
        :param pitch: Pitch of camera
        :param yaw: Yaw of camera
        """

        self.pos = pos.astype(float)
        self.resolution = resolution
        self.width = resolution[0]
        self.height = resolution[1]
        self.fov = fov
        self.pitch = pitch
        self.yaw = yaw

        self.distance = self.width * 0.5 / math.tan(math.radians(self.fov * 0.5))
        self.directions = self.updateRayDirections()




    def updateRayDirections(self):
        """

        :return: height x width x direction array of normalised ray direction vectors
        """

        dirs = np.zeros((self.height, self.width, 3))
        # [row1, row2, ...]

        topLeft = self.pos + np.array([-self.width * 0.5, self.height * 0.5, self.distance])
        goRight = np.array([1.0, 0.0, 0.0])
        goDown = np.array([0.0, -1.0, 0.0])

        pitchRads = math.radians(self.pitch)
        yawRads = math.radians(self.yaw)


        sinPitch = math.sin(pitchRads)
        sinYaw = math.sin(yawRads)
        cosPitch = math.cos(pitchRads)
        cosYaw = math.cos(yawRads)


        goRight = rotY(rotX(goRight, sinPitch, cosPitch), sinYaw, cosYaw)
        goDown = rotY(rotX(goDown, sinPitch, cosPitch), sinYaw, cosYaw)

        for y in range(self.height):
            rowStart = topLeft + goDown * y
            for x in range(self.width):
                pos = rowStart + goRight * x
                vec = pos - self.pos
                dirs[y][x] = vec / np.linalg.norm(vec)

        return dirs

    def render(self):
        result = np.zeros((self.height, self.width, 3))

        startTime = time.time()
        for y in range(self.height):
            if y%10 == 1:
                currentTime = time.time()
                progress = y / self.height
                elapsed = currentTime - startTime
                eTotal = (elapsed) / progress
                eRemaining = eTotal - elapsed
                print(f"Render progress: {y/self.height*100:.2f}%, elapsed: {elapsed:.2f}s, remaining: {eRemaining:.2f}s, total: {eTotal:.2f}s")
            for x in range(self.width):
                result[y][x] = rayCast(self.directions[y][x], self.pos)
        print("Render complete")
        print(f"Casted {raysCast} rays")
        return result


INV_255 = 1/255

def rayCast(ray:np.ndarray, origin:np.ndarray, ignore = [], depth = 0):
    """

    :param ray:
    :param origin:
    :return: Color
    """
    global raysCast
    raysCast += 1

    hitSomething = False
    closestObject = None
    closestDist = math.inf
    closestPoint = None
    closestReflected = None

    for object in world:
        if object.id in ignore:
            continue
        hit, hitPoint, travelDist, reflectedDirection = object.rayIntersects(ray, origin)
        if hit:
            if travelDist < closestDist:
                closestObject = object
                closestDist = travelDist
                closestPoint = hitPoint
                closestReflected = reflectedDirection
                hitSomething = True
    if hitSomething:
        if closestObject.reflectiveness>0:
            if depth < maxDepth:
                reflectedColor = rayCast(closestReflected, closestPoint, ignore = closestObject.siblings + [closestObject.id], depth = depth + 1)
                return (reflectedColor * closestObject.reflectiveness + closestObject.color * (1-closestObject.reflectiveness))
            return np.array([0, 0, 0])
        return closestObject.color



    sunness = np.dot(ray, sunDirection)
    if sunness < (1-sunSize):
        return skyColor
    coolness = (sunness - (1-sunSize)) / sunSize
    return np.array([255,255,255]) * coolness + skyColor * (1 - coolness)




screenScale = 1
sunDirection = normaliseVec(np.array([.5, 3, 1]))
skyColor = np.array([5, 192, 235])
sunSize = 2
maxDepth = 100


resolution = (1280, 720)
pygame.init()
screen = pygame.display.set_mode((resolution[0] * screenScale, resolution[1] * screenScale))
clock = pygame.time.Clock()





world = []
mainCam = Camera(pos=np.array([0.001, 0, 0]), resolution=resolution, fov = 130)

# world.append(Triangle(np.array([0, -10, 10]), np.array([10, 0, 6]), np.array([0, 10, 10]), reflectiveness=1))
#
# world.append(Triangle(np.array([-5, -5, 5]), np.array([0, -5, 5]), np.array([-5, 5, 2]), reflectiveness=.7, color = np.array([200, 20, 20])))

sideLength = 20
topX = 0
topY = 3**0.5/3*sideLength
leftX =-sideLength/2
leftY = -3**0.5/6*sideLength
rightX = sideLength/2
rightY = -3**0.5/6*sideLength

p1 = Plane([leftX, leftY, 0], [leftX*1.1, leftY*1.1, 200], [topX*1.1, topY*1.1, 200], [topX, topY, 0], color = np.array([220,20,20]),reflectiveness=.95)
p1.add()

p2 = Plane([rightX, rightY, 0], [rightX*1.1, rightY*1.1, 200], [topX*1.1, topY*1.1, 200], [topX, topY, 0], color = np.array([20,20,220]),reflectiveness=.95)
p2.add()

p3 = Plane([leftX, leftY, 0], [leftX*1.1, leftY*1.1, 200], [rightX*1.1, rightY*1.1, 200], [rightX, rightY, 0], color = np.array([20,220,20]),reflectiveness=.95)
p3.add()

raysCast = 0
result = mainCam.render()
surface = pygame.surfarray.make_surface(result.swapaxes(0, 1))
surface = pygame.transform.scale_by(surface, screenScale)





running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(surface, (0, 0))
    pygame.display.update()
    clock.tick(30)

pygame.quit()
