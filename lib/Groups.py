# construct groups of connected images.  The inclusion order favors
# images with the most connections (features matches) to neighbors.

import cv2
import json
import numpy as np
import os
import sys

# this builds a simple set structure that records if any image has any
# connection to any other image
def countFeatureConnections(image_list, matches):
    for image in image_list:
        image.connection_set = set()
    for i, match in enumerate(matches):
        for mi in match[1:]:
            for mj in match[1:]:
                if mi != mj:
                    image_list[mi[0]].connection_set.add(mj[0])
    for i, image in enumerate(image_list):
        # print image.name
        # for j in image.connection_set:
        #     print '  pair len', j, len(image.match_list[j])
        image.connection_count = len(image.connection_set)
        # print image.name, i, image.connection_set
        for j in range(len(image.match_list)):
            size = len(image.match_list[j])
            if size > 0 and not j in image.connection_set:
                print('  matches, but no connection')
        
def updatePlacedFeatures(placed_images, matches, placed_features):
    for i, match in enumerate(matches):
        count = 0
        if len(match[1:]) > 2:
            for m in match[1:]:
                if m[0] in placed_images:
                    count += 1
        placed_features[i] = count

# This is the current, best grouping function to use
def groupByFeatureConnections(image_list, matches):
    countFeatureConnections(image_list, matches)
    print("Start of top level grouping algorithm...")

    # start with no placed images or features
    placed_images = set()
    groups = []
    placed_features = [0] * len(matches)

    # wipe connection order for all images
    for image in image_list:
        image.connection_order = -1

    done = False
    while not done:
        print("Start of new group...")
        # start a fresh group
        group_images = set()
        
        # find the unplaced feature with the most connections to other
        # images
        max_connections = 2
        max_index = -1
        for i, match in enumerate(matches):
            if placed_features[i] == 0 and len(match[1:]) > max_connections:
                max_connections = len(match[1:])
                max_index = i
        if max_index == -1:
            break
        print('Feature with max connections (%d) = %d' % (max_connections, max_index))
        print('Starting group with:')
        match = matches[max_index]
        for m in match[1:]:
            group_images.add(m[0])
            placed_images.add(m[0])
            print(' ', image_list[m[0]].name)
        updatePlacedFeatures(placed_images, matches, placed_features)
        
        while True:
            # find the unplaced image with the most connections into
            # the placed set

            # per image counter
            image_counter = [0] * len(image_list)

            # count up the placed feature references to unplaced images
            for i, match in enumerate(matches):
                # only proceed if this feature has been placed (i.e. it
                # connects to two or more placed images)
                if placed_features[i] >= 1:
                    for m in match[1:]:
                        if not m[0] in placed_images:
                            image_counter[m[0]] += 1
            # print 'connected image count:', image_counter
            new_index = -1
            max_connections = -1
            for i in range(len(image_counter)):
                if image_counter[i] > max_connections:
                    new_index = i
                    max_connections = image_counter[i]
            if max_connections >= 25:
                print("New image with max connections:", image_list[new_index].name, "features:", max_connections)
                placed_images.add(new_index)
                group_images.add(new_index)
            else:
                if len(group_images) > 1:
                    groups.append(list(group_images))
                else:
                    done = True
                break

            updatePlacedFeatures(placed_images, matches, placed_features)

            new_image = image_list[new_index]
            new_image.connection_order = len(placed_images) - 1
            print('Added: {} groups: {} in current group {} total: {}'.format(new_image.name, len(groups)+1, len(group_images), len(placed_images)))
            
    # add all unplaced images in their own groups of 1
    for i, image in enumerate(image_list):
        if not i in placed_images:
            groups.append( [i] )
            
    print(groups)
    return groups


# for the specified image estimate the image area covered by
# connections to placed images.
def estimateConnectionArea(image):
    pass


# another idea ...
def groupByConnectedArea(image_list, matches):
    countFeatureConnections(image_list, matches)
    print("Start of top level grouping algorithm...")

    # start with no placed images or features
    placed_images = set()
    groups = []
    placed_features = [False] * len(matches)

    # wipe connection order for all images
    for image in image_list:
        image.connection_order = -1

    done = False
    while not done:
        print("Start of new group...")
        # start a fresh group
        group_images = set()
        
        # find the unplaced image with the most connections to other
        # images
        max_connections = 0
        max_index = -1
        for i, image in enumerate(image_list):
            print(image.connection_count)
            if image.connection_order < 0 and image.connection_count > max_connections:
                max_connections = image.connection_count
                max_index = i
        max_image = image_list[max_index]
        max_image.connection_order = 0
        print("Image with max connections: {} num: {}".format(max_image.name, max_connections))
        placed_images.add(max_index)
        group_images.add(max_index)
        updatePlacedFeatures(placed_images, matches, placed_features)

        while True:
            # find the unplaced image with the largest connection area
            # into the placed set

            # per image counter
            # image_counter = [0] * len(image_list)

            # clear the placed feature lists
            for i, image in enumerate(image_list):
                image.placed_feature_list = []
                    
            # assemble the placed feature lists for each unplaced image
            for i, match in enumerate(matches):
                # only proceed if this feature has been placed (i.e. it
                # connects to two or more placed images)
                if placed_features[i]:
                    for m in match[1:]:
                        if not m[0] in placed_images:
                            uv = image_list[m[0]].uv_list[m[1]]
                            image_list[m[0]].placed_feature_list.append(uv)

            # find the minarearect bounds for each the connected
            # points in each image
            for image in image_list:
                if len(image.placed_feature_list):
                    center, (w, h), angle = cv2.minAreaRect(np.array(image.placed_feature_list))
                    print('{} {} {}'.format(w, h, w*h))
                    image.connected_area = w*h
            
            # print 'connected image count:', image_counter
            new_index = -1
            max_area = -1
            for i, image in enumerate(image_list):
                if len(image.placed_feature_list):
                    if image.connected_area > max_area:
                        new_index = i
                        max_area = image.connected_area
            # fixme: should be automatic or something
            if max_area >= 15000:
                print("New image with max area:", image_list[new_index].name)
                print("  area:", image_list[new_index].connected_area)
                placed_images.add(new_index)
                group_images.add(new_index)
            else:
                if len(group_images) > 1:
                    groups.append(list(group_images))
                else:
                    done = True
                break

            updatePlacedFeatures(placed_images, matches, placed_features)

            new_image = image_list[new_index]
            new_image.connection_order = len(placed_images) - 1
            print('Added: {} groups: {} in current group: {} total: {}'.format(new_image.name, len(groups)+1, len(group_images), len(placed_images)))
            
    # add all unplaced images in their own groups of 1
    for i, image in enumerate(image_list):
        if not i in placed_images:
            groups.append( [i] )
            
    print(groups)
    return groups

# return the number of connections into the placed set
def numPlacedConnections(image, proj):
    count = 0
    for key in image.match_list:
        i2 = proj.findImageByName(key)
        if i2.group_starter:
            # artificially inflate count if we are connected to a group starter
            count += 1
        if i2.placed:
            count += 1
    return count

def groupByImageConnections(proj):
    # reset the cycle distance for all images
    for image in proj.image_list:
        image.placed = False
        image.group_starter = False
        
    for image in proj.image_list:
        image.total_connections = 0
        for key in image.match_list:
            if proj.findImageByName(key):
                image.total_connections += 1
        #if image.total_connections > 1:
        #    print("%s: connections: %d" % (image.name, image.total_connections))

    group_list = []
    group = []
    done = False
    while not done:
        done = True
        best_index = -1
        # find the unplaced image with the most placed neighbors
        best_connections = 0
        for i, image in enumerate(proj.image_list):
            if not image.placed:
                connections = numPlacedConnections(image, proj)
                if connections > best_connections:
                    best_index = i
                    best_connections = connections
                    done = False
        if best_index < 0 or best_connections < 2:
            print("Cannot find an unplaced image with a double connected neighbor.")
            if len(group):
                # commit the previous group (if it exists)
                group_list.append(group)
                # and start a new group
                group = []
            # now find an unplaced image that has the most connections
            # to other images (new cycle start)
            max_connections = 0
            for i, image in enumerate(proj.image_list):
                if not image.placed:
                    if (image.total_connections > max_connections):
                        max_connections = image.total_connections
                        best_index = i
                        done = False
                        # print(" found image {} connections = {}".format(i, max_connections))
            if best_index >= 0:
                # group starter!
                print("Starting a new group with:",
                      proj.image_list[best_index].name)
                proj.image_list[best_index].group_starter = True
        if best_index >= 0:
            image = proj.image_list[best_index]
            image.placed = True
            print("Adding: {} (placed connections = {}, total connections = {})".format(image.name, best_connections, image.total_connections), )
            group.append(best_index)

    print("Group (cycles) report:")
    for group in group_list:
        #if len(group) < 2:
        #    continue
        print("group (size = {}):".format((len(group))))
        for i in group:
            image = proj.image_list[i]
            print("{} ({})".format(image.name, image.total_connections))
        print("")

    return group_list

def save(path, groups):
    file = os.path.join(path, 'groups.json')
    try:
        fd = open(file, 'w')
        json.dump(groups, fd, indent=4, sort_keys=True)
        fd.close()
    except:
        print('{}: error saving file: {}'.format(file, str(sys.exc_info()[1])))

def load(path):
    file = os.path.join(path, 'groups.json')
    try:
        fd = open(file, 'r')
        groups = json.load(fd)
        fd.close()
    except:
        print('{}: error loading file: {}'.format(file, str(sys.exc_info()[1])))
        groups = []
    return groups
