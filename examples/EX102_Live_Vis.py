# This script demonstrates the use of the show_live function
# show_live creates a vtk top level window that runs in a seperate
# thread, and can be updated without blocking for instance for use
# at the same time as a seperate gui
if __name__ == "__main__":
    import cadquery as cq
    from cadquery.vis import show_live
    import time

    print("""
    #--------------------------------------
    START DEMONSTRATION OF LIVE VIS
    If you dont see printed text while the box
    rotates, run python with the "-u" flag.
    #--------------------------------------
    """)

    box = cq.Workplane().box(5, 2, 1).val() #initial geometry

    viewer = show_live(box) #initial view

    for _ in range(36):
        box = box.rotate((0, 0, 0), (0, 0, 1), 10) #update the geometry
        viewer.update(box) #update the view
        time.sleep(0.2)
        print("doing other stuff over here", flush=True) #do some other stuff in the program in-between view updates without blocking anything


    print("""
    #--------------------------------------
    COMPLETED DEMONSTRATION OF LIVE VIS
    If you dont see printed text while the box
    rotates, run python with the "-u" flag.
    #--------------------------------------
    """)

    #viewer.close() #uncomment me if you want the window to close after rotations

    while True: #comment me out if you dont want to be able to continue interacting after the updates are demonstrated
        pass