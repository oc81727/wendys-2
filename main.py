import numpy as np
import math
import pygame
import time
import random
from numba import njit



#
#       Z
#       ^
#       |    Y
#       |   7
#       |  /
#       | /
#       |/
#       -------------> X
#

class Vec3d():
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z
		self.array = np.array([x, y, z])

	def setVec(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z
		self.array = np.array([x, y, z])

	def setX(self, x):
		self.x = x
		self.array[0] = x

	def setY(self, y):
		self.y = y
		self.array[1] = y

	def setZ(self, z):
		self.z = z
		self.array[2] = z

	def __repr__():
		return self.array

	def __str__():
		return f"[{self.x}, {self.y}, {self.z}]"

class Color():
	def __init__(self, r, g, b):
		self.r = r
		self.g = g
		self.b = b
		self.color = np.array([r, g, b])

	def setColor(self, r, g, b):
		self.r = r
		self.g = g
		self.b = b
		self.color = np.array([r, g, b])

	def setR(self, r):
		self.r = r
		self.color[0] = r

	def setG(self, g):
		self.g = g
		self.color[1] = g

	def setB(self, b):
		self.b = b
		self.color[2] = b

	def __repr__():
		return self.color

	def __str__():
		return f"[{self.r}, {self.g}, {self.b}]"

class BoundingBox():
	def __init__(self, pos1, pos2):
		self.pos1 = pos1
		self.pos2 = pos2
		if pos1[0] < pos2[0]:
			self.minX = pos1[0]
			self.maxX = pos2[0]
		else:
			self.minX = pos2[0]
			self.maxX = pos1[0]

		if pos1[1] < pos2[1]:
			self.minY = pos1[1]
			self.maxY = pos2[1]
		else:
			self.minY = pos2[1]
			self.maxY = pos1[1]

		if pos1[2] < pos2[2]:
			self.minZ = pos1[2]
			self.maxZ = pos2[2]
		else:
			self.minZ = pos2[2]
			self.maxZ = pos1[2]
		self.min = np.array([self.minX, self.minY, self.minZ])
		self.max = np.array([self.maxX, self.maxY, self.maxZ])

class AlignedCube:
	#anchor is the least xyz point
	def __init__(self, pos, size, color:Color, isMirror = False, reflectiveness = 0, darkiness = 0):
		self.size = size
		self.pos = np.array(pos)
		self.color = color
		self.boundingBox = BoundingBox(self.pos, self.pos + size)
		self.isMirror = isMirror
		self.reflectiveness = reflectiveness
		self.darkiness = darkiness


class AlignedCuboid:
	def __init__(self, pos, size, color:Color, isMirror = False, reflectiveness = 0, darkiness = 0):
		self.size = np.array(size)
		self.pos = np.array(pos)
		self.color = color
		self.boundingBox = BoundingBox(self.pos, self.pos + self.size)
		self.isMirror = isMirror
		self.reflectiveness = reflectiveness
		self.darkiness = darkiness


class Triangle:
	def __init__(self, p1, p2, p3, color:Color, isMirror = False, reflectiveness = 0, darkiness = 0):
		self.p1 = np.array(p1)
		self.p2 = np.array(p2)
		self.p3 = np.array(p3)
		self.v0 = self.p1 - self.p3
		self.v1 = self.p2 - self.p3
		self.color = color
		self.normal = np.cross(self.v0, self.v1)
		self.normal = self.normal / np.linalg.norm(self.normal)
		minX = min(p1[0], p2[0], p3[0])
		minY = min(p1[1], p2[1], p3[1])
		minZ = min(p1[2], p2[2], p3[2])
		maxX = max(p1[0], p2[0], p3[0])
		maxY = max(p1[1], p2[1], p3[1])
		maxZ = max(p1[2], p2[2], p3[2])
		self.boundingBox = BoundingBox(np.array([minX,minY,minZ]), np.array([maxX,maxY,maxZ]))

		self.dot00 = self.v0 @ self.v0
		self.dot01 = self.v0 @ self.v1
		self.dot11 = self.v1 @ self.v1
		self.denom = self.dot00 * self.dot11 - self.dot01**2
		self.reflectiveness = reflectiveness
		self.darkiness = darkiness
		self.isMirror = isMirror

	def pointInTriangle3D(self, point):
		v2 = point - self.p3
		dot02 = self.v0 @ v2
		dot12 = self.v1 @ v2
		i = (self.dot11 * dot02 - self.dot01 * dot12) / self.denom
		j = (self.dot00 * dot12 - self.dot01 * dot02) / self.denom

		if i > 0 and j > 0 and (i + j) < 1:
			return True
		return False


	def triangleCheck(self, pos, direction):
		if rayIntersectsPlane(direction, self.normal):
			if self.pointInTriangle3D(rayPlaneIntersection(pos, direction, self.normal, self.p1)):
				return True
		return False

		
numPix = 0


class Camera:
	def __init__(self, pos, fov, width, height, pitch, yaw):
		self.pos = np.array(pos)
		self.fov = fov
		# self.length = length
		self.width = width
		self.height = height
		self.pitch = pitch
		self.yaw = yaw
		self.length = math.cos(deg2Rad(fov/2))*width/2



	def render(self):
		global numPix
		# ignoring camera direction for now # camera direction done
		array = np.zeros((self.height, self.width, 3), dtype=np.uint8) # swapped width and height
		#topLeft = self.pos.array + np.array([-self.width/2, self.length, self.height/2])
		wPitch = deg2Rad(-self.pitch)+math.pi/2
		wYaw = deg2Rad(self.yaw)
		xRotated = rotateZ(rotateX(np.array([1, 0, 0]), wPitch), wYaw)
		yRotated = rotateZ(rotateX(np.array([0, 1, 0]), wPitch), wYaw)
		zRotated = rotateZ(rotateX(np.array([0, 0, 1]), wPitch), wYaw)
		screenCenter = self.pos + self.length * yRotated
		topLeft = screenCenter - xRotated*self.width/2 + zRotated*self.height/2
		for y in range(self.height):
			if y%10 == 0:
				percent = max(round((y/self.height)*100,1),0.1)
				passed = time.time()
				eta = round((passed-startTime)/percent*(100) - (passed-startTime), 1)
				total = round((passed-startTime)/percent*100,1)
				print(f"render progress: {percent}%, eta: ({eta}s/{total}s)")
			for x in range(self.width):
				# pixPos = topLeft + np.array([x, 0, -y])
				pixPos = topLeft + xRotated*x - yRotated*y
				#try:
				array[y,x] = rayTrace(self.pos, normaliseVec(pixPos-self.pos))
				numPix += 1
				#except:
				#	print("that one error")
				#	print(f"x: {x}, y: {y}")

		return array



times = {}
runTimes = {}
startTimes = {}
def timeMe(func):
	global times,startTimes,runTimes
	if not func.__name__ in times:
		times[func.__name__] = 0
		runTimes[func.__name__] = 0
	def inner(*args, **kwargs):
		startTimes[func.__name__] = time.time()
		result = func(*args, **kwargs)
		end = time.time()
		times[func.__name__] += end - startTimes[func.__name__]
		runTimes[func.__name__] += 1
		return result
	return inner

@timeMe
def rotateX(vec, rads):
	rotMat = np.array([
		[1, 0, 0],
		[0, np.cos(rads), -np.sin(rads)],
		[0, np.sin(rads), np.cos(rads)]])
	return np.dot(vec, rotMat)

@timeMe
def rotateY(vec, rads):
	rotMat = np.array([
		[np.cos(rads), 0, np.sin(rads)],
		[0, 1, 0],
		[-np.sin(rads), 0, np.cos(rads)]])
	return np.dot(vec, rotMat)

@timeMe
def rotateZ(vec, rads):
	rotMat = np.array([
		[np.cos(rads), -np.sin(rads), 0],
		[np.sin(rads), np.cos(rads), 0],
		[0, 0, 1]])
	return np.dot(vec, rotMat)

@timeMe
def normaliseVec(vec):
	return vec/np.linalg.norm(vec)
	# return Vec3d(*(Vec3d.array/np.linalg.norm(Vec3d.array)))

@timeMe
def angleWithHorizon(vec):
	return math.degrees(math.asin(vec[2]/(np.linalg.norm(vec))))

hitMirror = 0

raysCast = 0



HALF_PI = 1.57079632679






@timeMe
@njit
def boundingBoxCheck(bb1, bb2, pos, direction):



	#find min and max travel distance for each axis
	#if there is a number that is in between all 3 min and max pairs then intersection
	#start + dist*direction = target  =>  dist = (target-start)/direction



	distX1 = (bb1[0]-pos[0])/direction[0]
	distX2 = (bb2[0]-pos[0])/direction[0]

	distY1 = (bb1[1]-pos[1])/direction[1]
	distY2 = (bb2[1]-pos[1])/direction[1]

	distZ1 = (bb1[2]-pos[2])/direction[2]
	distZ2 = (bb2[2]-pos[2])/direction[2]

	# dist1 = (bb1-pos)/direction
	# dist2 = (bb2-pos)/direction



	if distX1<distX2:
		minDX = distX1
		maxDX = distX2
	else:
		minDX = distX2
		maxDX = distX1

	if distY1<distY2:
		minDY = distY1
		maxDY = distY2
	else:
		minDY = distY2
		maxDY = distY1

	if distZ1<distZ2:
		minDZ = distZ1
		maxDZ = distZ2
	else:
		minDZ = distZ2
		maxDZ = distZ1

	# tmin = max(minDX, minDY, minDZ)
	# tmax = min(maxDX, maxDY, maxDZ)


	# min(a,b,c)
	# a if (a<b and a<c) else (b if b<c and b<a else c)
	# (a if a<c else c) if (a<b) else (b if b<c else c)   # fastest

	tmin = max(distX1 if distX1<distX2 else distX2, distY1 if distY1<distY2 else distY2, distZ1 if distZ1<distZ2 else distZ2)
	tmax = min(distX1 if distX1>distX2 else distX2, distY1 if distY1>distY2 else distY2, distZ1 if distZ1>distZ2 else distZ2)

	# tmin = max(min(dist1[0],dist2[0]), min(dist1[1],dist2[1]), min(dist1[2],dist2[2]))
	# tmax = min(max(dist1[0],dist2[0]), max(dist1[1],dist2[1]), max(dist1[2],dist2[2]))

	

	if 0 <= tmin <= tmax: # intersects
		return tmin
	else:
		return None

def rayTrace(pos, direction, recursionDepth = 0):
	# pos = pos.array # [x,y,z]
	global hitMirror, raysCast
	raysCast += 1

	# hehe im lazy
	if direction[0]==0:
		direction[0]=0.001
	if direction[1]==0:
		direction[1]=0.001
	if direction[2]==0:
		direction[2]=0.001

	#direction = normaliseVec(direction).array # [x,y,z]
	closestEntity = None
	closestEntityDist = math.inf
	for entity in world.objects:
		bb1 = entity.boundingBox.min # [x,y,z] of 1 corner
		bb2 = entity.boundingBox.max # [x,y,z] of opposite corner
		dist = boundingBoxCheck(bb1, bb2, pos, direction)
		if dist == None:
			continue
		if dist < closestEntityDist:
			closestEntityDist = dist
			closestEntity = entity


	if closestEntity != None:
		if isinstance(closestEntity, AlignedCube) or isinstance(closestEntity, AlignedCuboid):
			hitPoint = pos+closestEntityDist*direction
			bb1 = closestEntity.boundingBox.min
			bb2 = closestEntity.boundingBox.max
			hitSide = None
			if isBetween(hitPoint[0],bb1[0],bb2[0]):
				if isBetween(hitPoint[2],bb1[2],bb2[2]): # y
					hitSide = 1 
				elif isBetween(hitPoint[1],bb1[1],bb2[1]): # z
					hitSide = 2
			elif isBetween(hitPoint[2],bb1[2],bb2[2]) and isBetween(hitPoint[1],bb1[1],bb2[1]): # x
				hitSide = 0
			if hitSide == None:
				return closestEntity.color.color

			isOpposite = direction[hitSide] > 0

			# angle = rad2Deg(math.acos(direction[hitSide]/np.linalg.norm(direction)))
			angle = math.acos(direction[hitSide])
			# angle between 0 and pi/2
			# when 0, original color
			# when pi/2, return other color

			# angle between 0 and 90
			# when 0, return original color
			# when 90, return other color

		
			
			if recursionDepth>10:
				return np.array([0,0,0])
			if hitSide == 0:
				reflectedDirection = direction*np.array([-1,1,1])
			elif hitSide == 1:
				reflectedDirection = direction*np.array([1,-1,1])
			elif hitSide == 2:
				reflectedDirection = direction*np.array([1,1,-1])
			

			if closestEntity.reflectiveness != 0 or closestEntity.isMirror:
				
				reflectedColor = rayTrace(hitPoint, reflectedDirection,recursionDepth+1)
			
			if closestEntity.isMirror:
				hitMirror+=1
				# if hitMirror%50==0:
				# 	return closestEntity.color.color
				return filterColor(closestEntity.color.color,reflectedColor)


			if closestEntity.reflectiveness != 0:
				if isOpposite:
					mirrorProcessed = reflectedColor * angle
				mirrorProcessed = reflectedColor * HALF_PI
			else:
				mirrorProcessed = np.array([0,0,0])

			if closestEntity.darkiness != 0:
				if isOpposite:
					darkProcessed = np.array([0,0,0]) * angle
				darkProcessed = np.array([0,0,0]) * HALF_PI
			else:
				darkProcessed = np.array([0,0,0])

			return (closestEntity.color.color + darkProcessed*closestEntity.darkiness + filterColor(closestEntity.color.color,mirrorProcessed)*closestEntity.reflectiveness) / (1+closestEntity.reflectiveness + closestEntity.darkiness)
			#return mirrorProcessed*closestEntity.reflectiveness+darkProcessed*(1-closestEntity.reflectiveness)
			

			# if isOpposite:
			# 	return (closestEntity.color.color * (90 - angle) + np.array([0,0,0]) * angle) + reflectedColor*angle*closestEntity.reflectiveness / (90+closestEntity.reflectiveness*90)
			# return (closestEntity.color.color * (angle) + np.array([0,0,0]) * (90-angle)) + reflectedColor*(90-angle)*closestEntity.reflectiveness / (90+closestEntity.reflectiveness*90)
			# #
		#return closestEntity.color.color

		if isinstance(closestEntity, Triangle):
			if recursionDepth > 10:
				return np.array([0,0,0])
			check = closestEntity.triangleCheck(pos, direction)
			if check:
				color = closestEntity.color.color
				
				angle = 90 - rad2Deg(math.acos(np.dot(direction, closestEntity.normal)/(np.linalg.norm(direction))))
				# return (color * (90-angle)) / 90
				darkProcessed = (color * (90-angle)) / 90


				if closestEntity.reflectiveness != 0 or closestEntity.isMirror:
					hitPoint = rayPlaneIntersection(pos, direction, closestEntity.normal, closestEntity.p1)
					reflectedDirection = direction - 2*(np.dot(direction,closestEntity.normal))*closestEntity.normal
					reflectedColor = rayTrace(hitPoint+reflectedDirection*0.0001, reflectedDirection,recursionDepth+1)

					if closestEntity.isMirror:
						return reflectedColor
				
					
					mirrorProcessed = (reflectedColor * (90-angle)) / 90
				else:
					reflectedColor = np.array([0, 0, 0])

				return color + darkProcessed * closestEntity.darkiness + filterColor(color, reflectedColor) * closestEntity.reflectiveness / (1 + closestEntity.reflectiveness + closestEntity.darkiness)









	#pitch = angleWithHorizon(direction)
	#awesomeness = progressBetween(-90,90,pitch)

	sunness = angleWithDirection(direction,np.array([10,100,100]), False) # between 0 and pi
	#awesomeness = progressBetween(180,0,sunness)
	awesomeness = sunness * INV_PI


	#return np.array([255,255,255])*awesomeness+np.array([0,0,0])*(1-awesomeness)
	return np.array([255,255,255])*awesomeness+np.array([9,210,235])*(1-awesomeness)

		#return [255,255,255] # doesnt intersect

INV_PI = 1/math.pi

@timeMe
@njit
def filterColor(c1, c2):
	return c2*0.00392156863*c1
	#return c2/255*c1
	#return (c1/255)*(c2/255)*255


@timeMe
def progressBetween(b1,b2,val):
	return (val-b1)/(b2-b1)

@timeMe
@njit
def isBetween(num, a, b, threshold=1e-6):
    lower = a if a<b else b + threshold
    upper = a if a>b else b - threshold
    return lower < num < upper


@timeMe
def rad2Deg(rad):
	return rad/math.pi*180
@timeMe
def deg2Rad(deg):
	return deg/180*math.pi

@timeMe
def angleWithAxis(direction, axis, deg = True):
	if deg:
		return rad2Deg(math.acos(direction[axis]/np.linalg.norm(direction)))
	return math.acos(direction[axis]/np.linalg.norm(direction))
@timeMe
def angleWithDirection(d1, d2, deg = True):
	if deg:
		return rad2Deg(math.acos(np.dot(d1, d2)/(np.linalg.norm(d1)*np.linalg.norm(d2))))
	return math.acos(np.dot(d1, d2)/(np.linalg.norm(d1)*np.linalg.norm(d2)))

@timeMe
def rayIntersectsPlane(rayDirection, normal):
	if np.dot(rayDirection, normal) == 0:
		return False
	return True



@timeMe
def vecProject(a, b): #projecting a onto b
	return (np.dot(b, a)/np.dot(b, b)) * b
@timeMe
def rayPlaneIntersection(start, direction, normal, point):
	w = point - start
	k = np.dot(w, normal)/np.dot(direction, normal)
	return start + k * direction



# def pointInTriangle(a, b, c, p):
	# w2 = (a[0]*(b[1] - a[1]) + (p[1] - a[1])*(b[0] - a[0]) - p[0]*(b[1] - a[1])) / ((c[1] - a[1])*(b[0] - a[0]) - (c[0] - a[0])*(b[1] - a[1]))
	# if w2 < 0:
	# 	return False
	# w1 = (p[1] - a[1] - w2*(c[1] - a[1]))/(b[1] - a[1])
	# if w1 < 0:
	# 	return False
	# if w1 + w2 > 1:
	# 	return False
	# return True
# def pointInTriangle3D(a, b, c, p):
# 	w1 = (a[0]*(c[1]-a[1])+(p[1]-a[1])*(c[0]-a[0])-p[0]*(c[1]-a[1]))/((b[1]-a[1])*(c[0]-a[0])-(b[0]-a[0])*(c[1]-a[1]))
# 	w2 = (p[1]-a[1]-w1*(b[1]-a[1]))/(c[1]-a[1])
# 	if w2<0 or w1<0 or w2+w1 > 1:
# 		return False
# 	return True

# def pointInTriangle3D(a, b, c, p):
# 	v0 = a - c  # pre-calculate
# 	v1 = b - c  # pre-calculate
# 	v2 = p - c


# 	dot00 = v0 @ v0 # pre-calculate
# 	dot01 = v0 @ v1 # pre-calculate
# 	dot02 = v0 @ v2
# 	dot11 = v1 @ v1 # pre-calculate
# 	dot12 = v1 @ v2


# 	denom = dot00 * dot11 - dot01**2  # pre-calculate
# 	i = (dot11 * dot02 - dot01 * dot12) / denom
# 	j = (dot00 * dot12 - dot01 * dot02) / denom

# 	if i > 0 and j > 0 and (i + j) < 1:
# 		return True
# 	return False




class World:
	def __init__(self):
		self.objects = []

	def add(self, *objects):
		for i in objects:
			self.objects.append(i)


pygame.init()
world = World()



# mainCam = Camera((0,-300,0), 100, 1280, 720, 0, 0)


# tri = Triangle((-200,20,-200),(200,-20,-200),(0,20,200), Color(0,0,0), reflectiveness = 1, darkiness = 0, isMirror = True)
# world.add(tri)


# cube = AlignedCube((200,200,0), 200, Color(255,0,0),reflectiveness = 1, darkiness = 1)
# world.add(cube)



# world.add(AlignedCube((-10,200,0), 200, Color(0,255,0),reflectiveness = 1, darkiness = 1))



mainCam = Camera((-350,-600,400), 100, 1280, 720, -20, 15) # 100 fov
cube = AlignedCube((200,200,0), 200, Color(255,0,0),reflectiveness = 0.4, darkiness = 0.6)

world.add(AlignedCube((-200,-200,-200), 200, Color(0,0,255),reflectiveness = 0.4, darkiness = 0.6))
world.add(cube)

ground = AlignedCuboid((-500,-500,-500), (1000,1000,1), Color(0,255,255), reflectiveness=0.4, darkiness = 0.6)
leftWall = AlignedCuboid((-500,-500,-500), (1,1000,1000), Color(255,255,0), reflectiveness=0.4, darkiness = 0.6)
back = AlignedCuboid((-500,500,-500), (1000,1,1000), Color(255,0,255), reflectiveness=0.4, darkiness = 0.6)
mirrorCube = AlignedCuboid((700,-200,-200),(100,500,700),Color(255,255,255),isMirror = True)

world.add(ground,leftWall,back,mirrorCube)


# backMirror = AlignedCuboid(Vec3d(-1000,500,-1000), Vec3d(4000,1,2000), Color(255,255,255), isMirror=True)

# #bigWall = AlignedCuboid(Vec3d(-1000,-600,-1000), Vec3d(4000,1,2000), Color(0,255,255), reflectiveness=0.07)

# world.add(backMirror)

# world.add(AlignedCube(Vec3d(2950,-250,299),100,Color(255,255,0),reflectiveness=0.001))

# for i in range(6):
# 	world.add(AlignedCube(Vec3d(random.randint(-400,2000),random.randint(-600,100),random.randint(-700,700)),random.randint(100,500),Color(*generate_vibrant_color()),reflectiveness=0.05))









screen = pygame.display.set_mode((1280,720))
print("starting render")
startTime = time.time()
# rendered = np.transpose(mainCam.render(),(1,0,2))
rendered = np.rot90(mainCam.render(), k=3)
print(f"number of pixels rendered: {numPix}")
print(f"mirror hits: {hitMirror}")
print(f"rays cast: {raysCast}")
surface = pygame.surfarray.make_surface(rendered)
print("done")
print(f"render took {round(time.time()-startTime,2)}s")
print(times)
print(runTimes)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    
    screen.blit(surface,(0,0))

    pygame.display.flip()
    time.sleep(0.2)
pygame.quit()