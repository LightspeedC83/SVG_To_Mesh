# Image To Mesh
## Goal & summary
The end goal of this project is to take in an image and create a mesh from it that can be used for 3D modeling or 3D printing.

## Image Processing
The program starts by taking in an image, it converts the image to black and white (by which I do not mean greyscale, but that every pixel is either black or white) based on a value if the average value of the RGB values of the pixel falls below, the pixel is considered black. We only care about the black pixels. We then do a flood fill algorithm on the image to identify a group ID number for each black pixel (white pixels have a group ID number of None). Then we find the border pixels of each group. This processing gives us the following 2D arrays in which the data for a particular pixel at coordiantes (x,y) is held:
- pixel_array - 2D array pixel_array[y][x] yeilds True if there is a black pixel at (x,y), False if not
- groupID_array - 2D array pixel_array[y][x] yeilds yeilds the group ID of a pixel at (x,y), None if there is not black pixel there
- boundary_pixels - 2D array boundary_pixels[y][x] yeilds True if there (x,y) has a boundary pixel, False if not
- points_by_group - a python list that holds groups, each group is a list of coordinate values
- bounary_points_by_group - a python list that holds lists of boundary pixels for each group

All of this processing is done with numpy arrays, which make the program much faster than if we used python's lists

Now, we want to uniformly reduce the boundary points for each group. This is because with large images, we'd get an overly complicated mesh thats hard to work with, diffiuclt to process, and would be especially difficult to manually adjust. To do this uniform reduction, we use a reduction factor (stored in 'reduction_factor' variable), which is number between 0 and 1 (except we actually set it's lower bound at 0.01 so we don't get absurdly high skip numbers or a divide by 0 error). If the reduction factor is 0.5 or less, obtain a skip index by 1/reduction_factor, going through the list of boundary points, every 1/reduction_factor points, we don't add the point in question to the new list of reduced boundary points. For example a reduction_factor of 0.25 would yeild 4 (ie. 1/0.25) as a skip index. meaning that going through the list, we eliminate every 4th point, yielding a new list of boundary points that is reduced by 25% (or 1/4th). If the reduction factor is greater than 0.5, we get a skip index of 1/(1-reduction_factor) and then instead of deleting a point every skip_index points through the list, we delete every point and spare each point at a multiple of skip_index.

Using this approach on the boundary_points_by_group point groups, does not produce uniform reduction in points. When saving test images, there could be long runs of points that had not been reduced at all and big gaps where too many had been reduced in one spot (ie. the point density was not preserved). This is because the points aren't in an order such that adjacent points are adjacent in the list, instead, their order is a result of the way the flood fill algorithm touched them. My first instinct was to use the sorted() function on the groups of boundary points before going through so that they'd be in order of (x,y) with priority on x values (ie. sorted by their x value and then their y value). But this also produces non-uniform reduction. My next thought was sorting the points based on their euclidean distance from the origin. This approach works better, but is still not completely uniform. The solution that worked was building a new list by doing a flood fill like algorithm on each border group, starting at a random point in the group. The flood fill had to be slightly modified to check in all eight possible point positions around the current point.

The good thing is that now that we've sorted the points such that points close to eachother are next to eachother, this property is preserved after the uniform reduction of points. So the reduced_boundaries list of boundary groups has points next to eachother that are next to eachother, this will be advantageous for the creation faces when we make the mesh. 

## Mesh creation
### What is an OBJ file?
This program will turn the image into a .obj file. For reference, see the [wikipedia page](https://en.wikipedia.org/wiki/Wavefront_.obj_file) for .obj files. Some main points of information about obj files that will be useful to understand this program are:
- a vertex is specified via a line starting with the letter v, followed by (x,y,z) coordinate
    - note that you can leave z coordinate blank and it assumes 0 when it's being read
- a face is defined by a line starting with the letter f, followed by a list of vertex_index/texture_index/normal_index
    - note that you can just define in terms of vertex_index (eg. f 1 2 3 4 would make a face using the 1st, 2nd, 3rd, and 4th vertices you define in the file, with edges in that order)
- comments in an obj file are preceded by a # character (just like python)

### creating faces based on the image
The mesh creation process is to go through each point in a group, add it to the obj file as a vertex, store the vertex index of that point and then go through the boundary points and add them as face (producing an n-gon face using the points in the group). The problem is that while the points in reduced_boundares are sorted enough (because it came from a reduction of sorted_boundary_points), they aren't completely sorted. They were mostly sorted, sorted enough that the reduction process was uniform enough. But the problem is the face creation from a boundary point list, making the face with just one vertex out of order could ruin the geometry of the mesh and obscure the shape we are trying to represent. The problem now is how do we efficiently sort points such that points next to eachother on the border are next to eachother in the list. This is essentially the same problem as before (but now it's slightly different because we know that most of the points that should be next to eachother on the boundary are next to eachother in the list). We could use a brute force algorithm goes through each point and calculates the two closest points to it on the boundary and makes sure that it's situated betweeen both of those points in the list (if not, then it inserts itself where it needs to be). However, this would be computationally expensive, becuase for each point in the border you'd have to check all the other points, yielding O(n^n) complexity, which is (in a word) poo-poo. Instead, we'll take advantage of the fact that the list is mostly in the order we want already. This algorgihtm is described below:
- we calculate the average distance between two adjacent points in the list
    - this will serve as a benchmark by which to measure the points in the list. points that are out of place, will be more likely to have a distance to their neighbor higher than the benchmark 
    - may also want to consider using the distance based on the skip_index (assuming the points in the list are directly adjacent before reduction, which is not an unfair assumption)
- go through each point in the list, get the distance to the next point, compare the distance to the benchmark, if the distance and benchmark values are off by some margin, then take that next point and insert it into the list where it should go (ie. the position where it has the smallest distance between itself and its two neighbors.)
    - because the list is already mostly correct, most of the points we relocate will actually be out of place. with fine tuning of benchmark calculation and margin, we should be able to get good preformance.

### Extending the mesh 
Once you have the points in order, extending the mesh to make the image 3D is pretty trivial, all you do is copy the faces we already made for each group, with an offset z-value. After this, we simply make a face with each point in the list, the next point in the list, and the two corresponding points on the offset face (the last point in the list wraps around to make a face with the first point in the list).