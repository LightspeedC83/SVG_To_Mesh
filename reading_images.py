import numpy as np
from PIL import Image
from collections import deque

#opening the reference image
reference_name = "test"
reference_path = f"images\{reference_name}.jpg"

reference_image = Image.open(reference_path)
reference_pixels = list(reference_image.getdata())
reference_size = reference_image.size # getting the refence image's size in (x-pixles,y-pixels) format
x_size = reference_size[0]
y_size = reference_size[1]


# making a greyscale version of the reference image
reference = []
for p in reference_pixels:
    avg = (p[0]+p[1]+p[2])/3
    reference.append((avg,avg,avg))

# take the greyscale image and make it purely black and white
bw_threshold = 50
bw_reference = []
for p in reference:
    if p[0] >= bw_threshold: #if the pixel has value over threshold (ie. pixel is too light), we make it white
        bw_reference.append((255,255,255))
    else: #if value is black enough, we make it black
        bw_reference.append((0,0,0))


# To store the data we want, we'll use a series of 2d Arrays. These will store: bw pixel value, group number, is this pixel an edge pixel for its group
 
#first we create an array for the black-white pixel value, black will be represented as True (1), white as False (0)
pixel_list = [] # a 2D list as specified
temp_list = []
for p in bw_reference: #converting all pixel values in bw_reference to 0s and 1s and storing them in pixel_list accordingly
    if len(temp_list) == reference_size[0]:
        pixel_list.append(temp_list)
        temp_list = []
    
    if p[0] == 0:
        temp_list.append(1)
    else:
        temp_list.append(0)
pixel_list.append(temp_list)

pixel_array = np.array(pixel_list,dtype=bool) # this stores booleans, true means there is a black pixel at said location, false means there is not a black pixel at said location



# now we do a flood fill to assign groupIDs to all pixel objects (white pixels have groupID None)
visited_spots = np.array([[0 for x in range(reference_size[0])]for y in range(reference_size[1])], dtype=bool) # a key of visited spots, False(0) means we haven't visited, True(1) means we have. use this for any given pixel to see if we've visited

points_by_group = []
groupID_array = np.array([[None for x in range(reference_size[0])]for y in range(reference_size[1])]) #2d array that stores the group id for a pixel at a point, None if it's a white pixel

group_index = 0
for y in range(reference_size[1]):
    for x in range(reference_size[0]):
        curr = pixel_array[y][x] # gives boolean: True if pixel is black, False if not

        if not visited_spots[y][x]: # if the pixel under consideration hasn't been visited

            if not curr: #if location does not have a white we mark as visited and move on
                visited_spots[y][x] = True 
            else:
                queue = deque() #create a queue
                queue.append((x,y)) 
                group = []
                while len(queue)!=0: #while queue isn't empty we keep looking at neighbors of the queue and assigning them IDs of said group
                    upNext = queue.pop()
                    groupID_array[upNext[1]][upNext[0]] = group_index #assigning the group index for this group
                    group.append(upNext)
                    visited_spots[upNext[1],upNext[0]] = True #marking this pixel as visited
                    for next_point in [[upNext[0]-1, upNext[1]], [upNext[0]+1, upNext[1]], [upNext[0], upNext[1]-1], [upNext[0], upNext[1]+1]]:
                        if next_point[0]>=0 and next_point[1]>=0 and next_point[0]<x_size and next_point[1]<y_size: #if location is valid 
                            if visited_spots[next_point[1]][next_point[0]] == 0 and pixel_array[next_point[1]][next_point[0]]: #if the pixel at the potential neighbor position isn't already visited and has a black pixel, we add to queue to check
                                queue.append((next_point[0],next_point[1])) 
                group_index +=1
                points_by_group.append(group)



# going through and marking the boundary pixels for each pixel group
boundary_pixles = np.array([[0 for x in range(reference_size[0])]for y in range(reference_size[1])], dtype=bool)
for y in range(reference_size[1]):
    for x in range(reference_size[0]):
        
        for next_point in [[x-1, y], [x+1, y], [x, y-1], [x, y+1]]: 
            if next_point[0]>=0 and next_point[1]>=0 and next_point[0]<x_size and next_point[1]<y_size: #if location is valid                          
                if not pixel_array[next_point[1]][next_point[0]] and groupID_array[y][x]!=None: #if the pixel at the potential neighbor position is white (remember True means black), we mark curr as a border pixel (curr also has to be part of a group)
                    boundary_pixles[y][x] = True
            elif groupID_array[y][x]!=None: #if a pixel that is part of a group is on a the border of the image, it's marked as a border pixel as well
                boundary_pixles[y][x] = True

boundary_points_by_group = []
for g in points_by_group:
    boundary = []
    for p in g:
        if boundary_pixles[p[1]][p[0]]:
            boundary.append(p)
    boundary_points_by_group.append(boundary)



# Now we have the following datastrucutres to keep track information about a pixel at a location (x,y)
#   pixel_array - 2D array pixel_array[y][x] yeilds True if there is a black pixel at (x,y), False if not
#   groupID_array - 2D array pixel_array[y][x] yeilds yeilds the group ID of a pixel at (x,y), None if there is not black pixel there
#   boundary_pixels - 2D array boundary_pixels[y][x] yeilds True if there (x,y) has a boundary pixel, False if not
#   points_by_group - a python list that holds groups, each group is a list of coordinate values
#   bounary_points_by_group - a python list that holds lists of boundary pixels for each group


# saving an image of all the border pixels marked in red
output_pixels = []
for y in range(reference_size[1]):
    for x in range(reference_size[0]):
        
        if boundary_pixles[y][x]:
            output_pixels.append((255,0,0))
        else:
            output_pixels.append((255,255,255))
        
reference_image = Image.new(mode="RGB", size=reference_size)
reference_image.putdata(output_pixels)
reference_image.save(f"images\{reference_name}_borders_marked.png")

# saving an image with all the pixels of the same group assigned the same random color
color_groups ={}
color_groups[None] = (255,255,255) #white if it's a white pixel

output_pixels = []
for y in range(reference_size[1]):
    for x in range(reference_size[0]):
        color = None
        try:
            color = color_groups[groupID_array[y][x]]
        except KeyError:
            color = (np.random.randint(0,250),np.random.randint(0,250),np.random.randint(0,250))
            color_groups[groupID_array[y][x]] = color
        if boundary_pixles[y][x]: #if it's a boundary pixel, we make it black
            color = (0,0,0)
        output_pixels.append(color)

reference_image = Image.new(mode="RGB", size=reference_size)
reference_image.putdata(output_pixels)
reference_image.save(f"images\{reference_name}_groups_marked.png")


# now what we want to do is reduce the number of pixels in each border group uniformly by a certain percentage
reduction_factor = 0.75 #the percentage by which we will reduce the each group list (0.5 reduces the list be one half, 0.25 reduces it by 1/4 (ie. it become 75% of its original size))
reduced_boundaries = []
for group in boundary_points_by_group:
    reduced_group = []
    if reduction_factor <= 0.5 and reduction_factor>=0.01: # lower bound so we don't get absurdly high numbers, negative numbers, or a divide by 0 error
        # TODO: figure out how to max out (adjust beneath) based on density of group for this edge        
        skip_num = round(1/reduction_factor)
        index = 0
        for p in group:
            if index%skip_num != 0: #every skip_num points, we don't add the current point to the list
                reduced_group.append(p)
            index+=1
    else:
        # TODO: figure out how to max out (adjust beneath) based on density of group for this edge    
        skip_num = round(1/(1-reduction_factor))
        index = 0
        for p in group:
            if index%skip_num == 0: #every skip_num points, we add the current point to the list
                reduced_group.append(p)
            index+=1

    reduced_boundaries.append(reduced_group)


# saving an image of all the border pixels (now reduced) marked in red
output_pixels = [[(255,255,255) for x in range(x_size)] for y in range(y_size)]
for g in reduced_boundaries:
    for p in g:
        output_pixels[p[1]][p[0]] = (255,0,0)

output = []
for y in output_pixels:
    for x in y:
        output.append(x)

reference_image = Image.new(mode="RGB", size=reference_size)
reference_image.putdata(output)
reference_image.save(f"images\{reference_name}_borders_reduced_by_{int(100*reduction_factor)}_percent.png")