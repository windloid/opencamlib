import ocl
import camvtk
import time
import vtk
import datetime
import math
import random
import os

def drawVertex(myscreen, p, vertexColor, rad=1):
    myscreen.addActor( camvtk.Sphere( center=(p.x,p.y,p.z), radius=rad, color=vertexColor ) )

def drawEdge(myscreen, e, edgeColor=camvtk.yellow):
    p1 = e[0]
    p2 = e[1]
    myscreen.addActor( camvtk.Line( p1=( p1.x,p1.y,p1.z), p2=(p2.x,p2.y,p2.z), color=edgeColor ) )

def drawFarCircle(myscreen, r, circleColor):
    myscreen.addActor( camvtk.Circle( center=(0,0,0), radius=r, color=circleColor ) )

def drawDiagram( myscreen, vd ):
    drawFarCircle(myscreen, vd.getFarRadius(), camvtk.pink)
    
    for v in vd.getGenerators():
        drawVertex(myscreen, v, camvtk.green, 2)
    for v in vd.getVoronoiVertices():
        drawVertex(myscreen, v, camvtk.red, 1)
    for v in vd.getFarVoronoiVertices():
        drawVertex(myscreen, v, camvtk.pink, 10)
    vde = vd.getVoronoiEdges()
    
    print " got ",len(vde)," Voronoi edges"
    for e in vde:
        drawEdge(myscreen,e, camvtk.cyan)

class VD:
    def __init__(self, myscreen, vd, scale=1):
        self.myscreen = myscreen
        self.gen_pts=[ocl.Point(0,0,0)]
        self.generators = camvtk.PointCloud(pointlist=self.gen_pts)
        self.verts=[]
        self.far=[]
        self.edges =[]
        self.generatorColor = camvtk.green
        self.vertexColor = camvtk.red
        self.edgeColor = camvtk.cyan
        self.vdtext  = camvtk.Text()
        self.vertexRadius = scale/100
        self.vdtext.SetPos( (50, myscreen.height-150) )
        self.Ngen = 0
        self.vdtext_text = ""
        self.setVDText(vd)
        self.scale=scale
        
        myscreen.addActor(self.vdtext)
        
    def setVDText(self, vd):
        self.Ngen = len( vd.getGenerators() )-3
        self.vdtext_text = "VD with " + str(self.Ngen) + " generators.\n"
        self.vdtext_text += "YELLOW = New point-generator/site\n"
        self.vdtext_text += "PINK = Seed vertex\n"
        self.vdtext_text += "RED = Delete vertices/edges\n"
        self.vdtext_text += "GREEN = Modified VD edges\n"
        self.vdtext.SetText( self.vdtext_text )
        
        
    def setGenerators(self, vd):
        if len(self.gen_pts)>0:
            myscreen.removeActor( self.generators ) 
        #self.generators=[]
        self.gen_pts = []
        for p in vd.getGenerators():
            self.gen_pts.append(self.scale*p)
        self.generators= camvtk.PointCloud(pointlist=self.gen_pts) 
        self.generators.SetPoints()
        myscreen.addActor(self.generators)
        self.setVDText(vd)
        myscreen.render() 
    
    def setFar(self, vd):
        for p in vd.getFarVoronoiVertices():
            p=self.scale*p
            myscreen.addActor( camvtk.Sphere( center=(p.x,p.y,p.z), radius=self.vertexRadius, color=camvtk.pink ) )
        myscreen.render() 
    
    def setVertices(self, vd):
        for p in self.verts:
            myscreen.removeActor(p)
        self.verts = []
        for pt in vd.getVoronoiVertices():
            p=self.scale*pt
            actor = camvtk.Sphere( center=(p.x,p.y,p.z), radius=self.vertexRadius, color=self.vertexColor )
            self.verts.append(actor)
            myscreen.addActor( actor )
            #draw clearance-disk
            """
            cir_actor = camvtk.Circle( center=(p.x,p.y,p.z), radius=math.sqrt(pt[1])*self.scale, color=self.vertexColor )
            self.verts.append(cir_actor)
            myscreen.addActor(cir_actor)
            """
        myscreen.render() 
        
    def setEdgesPolydata(self, vd):
        self.edges = []
        self.edges = vd.getEdgesGenerators()
        self.epts = vtk.vtkPoints()
        nid = 0
        lines=vtk.vtkCellArray()
        for e in self.edges:
            p1 = self.scale*e[0]
            p2 = self.scale*e[1] 
            self.epts.InsertNextPoint( p1.x, p1.y, p1.z)
            self.epts.InsertNextPoint( p2.x, p2.y, p2.z)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0,nid)
            line.GetPointIds().SetId(1,nid+1)
            nid = nid+2
            lines.InsertNextCell(line)
        
        linePolyData = vtk.vtkPolyData()
        linePolyData.SetPoints(self.epts)
        linePolyData.SetLines(lines)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(linePolyData)
        
        self.edge_actor = vtk.vtkActor()
        self.edge_actor.SetMapper(mapper)
        self.edge_actor.GetProperty().SetColor( camvtk.cyan )
        myscreen.addActor( self.edge_actor )
        myscreen.render() 

    def setEdges(self, vd):
        for e in self.edges:
            myscreen.removeActor(e)
        self.edges = []
        for e in vd.getEdgesGenerators():
            p1 = self.scale*e[0]  
            p2 = self.scale*e[1] 
            actor = camvtk.Line( p1=( p1.x,p1.y,p1.z), p2=(p2.x,p2.y,p2.z), color=self.edgeColor )
            myscreen.addActor(actor)
            self.edges.append(actor)
        myscreen.render() 
        
    def setAll(self, vd):
        self.setGenerators(vd)
        #self.setFar(vd)
        self.setVertices(vd)
        self.setEdges(vd)


def writeFrame( w2if, lwr, n ):
    w2if.Modified() 
    current_dir = os.getcwd()
    filename = current_dir + "/frames/vd500_zoomout"+ ('%05d' % n)+".png"
    lwr.SetFileName( filename )
    #lwr.Write()

def regularGridGenerators(far, Nmax):
    # REGULAR GRID
    rows = int(math.sqrt(Nmax))
    print "rows= ",rows
    gpos=[-0.7*far ,  1.4*far/float(rows-1) ]  # start, stride
    plist = []
    for n in range(rows):
        for m in range(rows):
            x=gpos[0]+gpos[1]*n
            y=gpos[0]+gpos[1]*m
            # rotation
            alfa = 0
            xt=x
            yt=y
            x = xt*math.cos(alfa)-yt*math.sin(alfa)
            y = xt*math.sin(alfa)+yt*math.cos(alfa)
            plist.append( ocl.Point(x,y) )
    random.shuffle(plist)
    return plist

def randomGenerators(far, Nmax):
    pradius = (1.0/math.sqrt(2))*far
    plist=[]
    for n in range(Nmax):
        x=-pradius+2*pradius*random.random()
        y=-pradius+2*pradius*random.random()
        plist.append( ocl.Point(x,y) )
    return plist
    
def circleGenerators(far, Nmax):
    # POINTS ON A CIRCLE
    #"""
    #cpos=[50,50]
    #npts = 100
    dalfa= float(2*math.pi)/float(Nmax-1)
    #dgamma= 10*2*math.pi/npts
    #alfa=0
    #ofs=10
    plist=[]
    radius=0.81234*far
    for n in range(Nmax):
        x=radius*math.cos(n*dalfa)
        y=radius*math.sin(n*dalfa)
        plist.append( ocl.Point(x,y) )
    random.shuffle(plist)
    return plist
    
    
if __name__ == "__main__":  
    print ocl.revision()
    myscreen = camvtk.VTKScreen()
    camvtk.drawOCLtext(myscreen)
    
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(myscreen.renWin)
    lwr = vtk.vtkPNGWriter()
    lwr.SetInput( w2if.GetOutput() )
    #w2if.Modified()
    #lwr.SetFileName("tux1.png")
    
    scale=1
    myscreen.render()
    random.seed(42)
    far = 1
    
    camPos = far
    zmult = 5
    myscreen.camera.SetPosition(camPos/float(1000), camPos/float(1000), zmult*camPos) 
    myscreen.camera.SetClippingRange(-(zmult+1)*camPos,(zmult+1)*camPos)
    myscreen.camera.SetFocalPoint(0.0, 0, 0)
    vd = ocl.VoronoiDiagram(far,1200)
    
    vod = VD(myscreen,vd,scale)
    #vod.setAll(vd)
    drawFarCircle(myscreen, vd.getFarRadius(), camvtk.orange)
    
    Nmax = 5
    
    plist = randomGenerators(far, Nmax)
    #plist = regularGridGenerators(far, Nmax)
    #plist = circleGenerators(far, Nmax)
    
    #print plist[169]
    #exit()
    n=1
    t_before = time.time() 
    #delay = 1.5 # 0.533
    delay = 0.1 # 0.533
    #ren = [1,2,3,4,5,59,60,61,62]
    #ren = [16,17]
    ren = range(0,Nmax)
    ren=[4,5]
    nf=0
    idx_list=[]
    pt_dict = {}
    for p in plist: #[0:20]:
        print "**********"
        print "PYTHON: adding generator: ",n," at ",p
        
        if n in ren:
            vod.setAll(vd)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        
        #GENERATOR
        #"""
        vertexRadius = float(far)/float(100)
        gp=scale*p
        gen_actor = camvtk.Sphere( center=(gp.x,gp.y,gp.z), radius=vertexRadius, color=camvtk.yellow )
        if n in ren:
            myscreen.addActor(gen_actor)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        #"""
            
        #SEED
        #"""
        sv = scale*vd.getSeedVertex(p)
        print " seed vertex is ",sv
        seed_actor = camvtk.Sphere( center=(sv.x,sv.y,sv.z), radius=vertexRadius, color=camvtk.pink )
        if n in ren:
            myscreen.addActor(seed_actor)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        #"""

        #DELETE-SET
        #"""
        delset = vd.getDeleteSet(p)
        #print " seed vertex is ",sv
        p_actors = []
        if n in ren:
            for pd in delset:
                pos = scale*pd[0]
                type = pd[1]
                p_actor = camvtk.Sphere( center=(pos.x,pos.y,pos.z), radius=vertexRadius, color=camvtk.red )
                p_actors.append(p_actor)
            for a in p_actors:
                myscreen.addActor(a)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        #"""
        
        #DELETE-EDGES
        #"""
        delEdges = vd.getDeleteEdges(p)
        modEdges = vd.getModEdges(p)
        #print " seed vertex is ",sv
        edge_actors = []
        if n in ren:
            for e in delEdges:
                p1 = scale*e[0]
                p2 = scale*e[1]
                e_actor = camvtk.Line( p1=( p1.x,p1.y,p1.z), p2=(p2.x,p2.y,p2.z), color=camvtk.red ) 
                edge_actors.append(e_actor)
            for e in modEdges:
                p1 = scale*e[0]
                p2 = scale*e[1]
                e_actor = camvtk.Line( p1=( p1.x,p1.y,p1.z), p2=(p2.x,p2.y,p2.z), color=camvtk.green ) 
                edge_actors.append(e_actor)
            for a in edge_actors:
                myscreen.addActor(a)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        #"""
        
        pt_idx = vd.addVertexSite( p )
        idx_list.append( pt_idx )
        pt_dict[pt_idx] = p
        
        #w2if.Modified() 
        #lwr.SetFileName("frames/vd500_"+ ('%05d' % n)+".png")
        #lwr.Write()
        
        if n in ren:
            vod.setAll(vd)
            myscreen.render()
            time.sleep(delay)
            writeFrame( w2if, lwr, nf )
            nf=nf+1
        
        if n in ren:
            myscreen.removeActor(gen_actor)
            myscreen.removeActor(seed_actor)
            for a in p_actors:
                myscreen.removeActor(a)
            for a in edge_actors:
                myscreen.removeActor(a)
        
        n=n+1
        #print "**********"
        
    t_after = time.time()
    calctime = t_after-t_before
    print "idx list is ", idx_list
    
    vd.addLineSite( idx_list[0], idx_list[1] )
    
    # draw segment endpoints
    start = pt_dict[idx_list[0]]
    end = pt_dict[idx_list[1]]
    p1_actor = camvtk.Sphere( center=(start.x,start.y,start.z), radius=vertexRadius, color=camvtk.yellow )
    p2_actor = camvtk.Sphere( center=(end.x,end.y,end.z), radius=vertexRadius, color=camvtk.yellow )
    myscreen.addActor(p1_actor)
    myscreen.addActor(p2_actor)
    
    vod.setAll(vd)
    myscreen.render()
            
    print " VD done in ", calctime," s, ", calctime/Nmax," s per generator"
        
    print "PYTHON All DONE."


    
    myscreen.render()    
    myscreen.iren.Start()