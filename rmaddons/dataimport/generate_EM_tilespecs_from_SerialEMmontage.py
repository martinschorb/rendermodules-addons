#!/usr/bin/env python
"""
Create tilespecs from SerialEM montages.
Currently only idoc files are supported.

"""

import os
import renderapi
from asap.module.render_module import StackOutputModule

from asap.dataimport.schemas import GenerateEMTileSpecsOutput

from rmaddons.dataimport.schemas import GenerateSerialEMTileSpecsParameters

from rmaddons.utilities.EMBL_file_utils import groupsharepath

import time

import pyEM as em

from subprocess import Popen, PIPE



example_input = {
    "render": {
        "host": "render.embl.de",
        "port": 8080,
        "owner": "SerialEM",
        "project": "test",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "image_file": "/g/emcf/schorb/data/serialem_montages/idocmont/test2.idoc",
    "stack": "test_1",
    "overwrite_zlayer": True,
    "pool_size": 4,
    "close_stack": True,
    "z_index": 1,
    "z_spacing": 100
}


class GenerateSEMmontTileSpecs(StackOutputModule):
    default_schema = GenerateSerialEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput


    def ts_from_SerialEMtile(self,tile,camline,header,z=0):
        """

        :param dict tile: :class:`pyEM.adoc_item` containg the montage slice
        :param str camline: line of the adoc file describing the camera settings
        :param list header:  header of the adoc
        :param int z: section index
        :return f1: path to the raw image of the tile
        :return tilespec: a :class:`renderapi.tilespec.TileSpec` object with the metadata for this tile

        """

        # curr_posid = [int(tile['tileid'].split('.')[0]),int(tile['tileid'].split('.')[1])]
        # curr_pos = tilepos[posid.index(str(curr_posid[0])+'.'+str(curr_posid[1]))]

   # 2) The translation matrix to position the object in space (lower left corner)
        # mat_t = np.concatenate((np.eye(3),[[tile['glob_x']],[tile['glob_y']],[tile['glob_z']]]),axis=1)
        # mat_t = np.concatenate((mat_t,[[0,0,0,1]]))

        f1 = os.path.realpath(tile['# [Image'])

        filepath= groupsharepath(f1)

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)

        pxs = float(tile['PixelSpacing'][0])/10 # in nm

        if 'SuperMontCoords' in tile:
            xpos=float(tile['SuperMontCoords'][0])
            ypos=float(tile['SuperMontCoords'][1])
        else:
            xpos=float(tile['PieceCoordinates'][0])
            ypos=float(tile['PieceCoordinates'][1])
            
            
        if 'AlignedPieceCoords' in tile:
            xpos = xpos + float(tile['AlignedPieceCoords'][0]) - float(tile['PieceCoordinates'][0])
            ypos = ypos + float(tile['AlignedPieceCoords'][1]) - float(tile['PieceCoordinates'][1])
        elif 'AlignedPieceCoordsVS' in tile:
            xpos = xpos + float(tile['AlignedPieceCoordsVS'][0]) - float(tile['PieceCoordinates'][0])
            ypos = ypos + float(tile['AlignedPieceCoordsVS'][1]) - float(tile['PieceCoordinates'][1])


        if 'UncroppedSize' in tile:
            width = abs(int(tile['UncroppedSize'][0]))
            height = abs(int(tile['UncroppedSize'][1]))
        else:
            width = int(header[0]['ImageSize'][0])
            height = int(header[0]['ImageSize'][1])


        if 'StagePosition' in tile and 'ImageShift' in tile:
            stageX = float(tile['StagePosition'][0]) + float(tile['ImageShift'][0])
            stageY = float(tile['StagePosition'][1]) + float(tile['ImageShift'][1])
        else:
            stageX = xpos * pxs
            stageY = ypos * pxs


        tf_trans = renderapi.transform.AffineModel(
                                 B0=xpos,
                                 B1=-ypos)

        tileid = tile['# [Image'].strip('.tif')


        print("Processing tile "+tileid+" metadata for Render.")


        ts = renderapi.tilespec.TileSpec(
            tileId=tileid,
            imagePyramid=ip,
            z=z,
            width=width,
            height=height,
            minint=0, maxint=65535,
            tforms=[tf_trans],
            sectionId=z,
            scopeId='SerialEM: ' + camline[camline.find('-')+1:].strip(' '),
            cameraId=camline[camline.find(':')+1:camline.find('-')].strip(' '),
            stageX = stageX,
            stageY = stageY,
            pixelsize = pxs # in nm
            )
        
        # json_file = os.path.realpath(os.path.join(tilespecdir,outputProject+'_'+outputOwner+'_'+outputStack+'_%04d.json'%z))
        # fd=open(json_file, "w")
        # renderapi.utils.renderdump(tilespeclist,fd,sort_keys=True, indent=4, separators=(',', ': '))
        # fd.close()

        return f1,ts


    def ts_from_serialemmontage (self,idocfile,mapsection=0,correct_gradient=True):
        """

        :param str idocfile: input file (idoc)
        :param int mapsection: if multiple montages inside the file, index of section to be imported
        :param correct_gradient: if intensity gradient correction should be performed (not yet implemented)
        :return: list of :class:`renderapi.tilespec.TileSpec` objects for all tiles.

        """
        rawdir = os.path.dirname(idocfile)
        os.chdir(rawdir)


        timestamp = time.localtime()
        if not os.path.exists('conv_log'):os.makedirs('conv_log')
        log_name = '_{}{:02d}{:02d}-{:02d}{:02d}'.format(timestamp.tm_year,timestamp.tm_mon,timestamp.tm_mday,timestamp.tm_hour,timestamp.tm_min)


        # mipmap_args = []
        # tilespecpaths = []
        logfile = os.path.join(rawdir,'conv_log','SerialEM_convert'+log_name+'.log')
        
        
        
        idoc = em.loadtext(idocfile)            
        
        i_info = em.parse_adoc(idoc)
        
        if 'ImageFile' in i_info.keys():
            #MRC file
            #imfile = i_info['ImageFile'][0]
            raise(FileNotFoundError('MRC not yet supported'))
        else:
            # Tif files and idoc       
            tiles = em.adoc_items(idoc, '[Image')    
            header = em.adoc_items(idoc, '', header=True)   
            camline = em.adoc_items(idoc,'[T =')[0]['# [T =']
        
        
        tspecs=[]
        
        for tile in tiles:              
            f1,tilespeclist = self.ts_from_SerialEMtile(tile, camline, header)

            if os.path.exists(f1):
                tspecs.append(tilespeclist)
            else:
                fnf_error = 'ERROR: File '+f1+' does not exist'
                print(fnf_error)
                with open(logfile,'w') as log: log.writelines(fnf_error)
        
        
        pxs = float(header[0]['PixelSpacing'][0])/10

        # print(pxs)
        
        allspecs = [tspecs,pxs]

        return allspecs #,mipmap_args


    def run(self):    
        specs = self.ts_from_serialemmontage(self.args["image_file"])
        z_res = self.args["z_spacing"]

        # create stack and fill resolution parameters
    
        pxs=specs[1]

        self.args["output_stackVersion"]["stackResolutionX"]=pxs
        self.args["output_stackVersion"]["stackResolutionY"]=pxs
        self.args["output_stackVersion"]["stackResolutionZ"]=z_res

        # self.args["output_stack"] = self.args["stack"]


        self.output_tilespecs_to_stack(specs[0])

# I don know what this does... so leave it out
        # try:
        #     self.output({'stack': self.output_stack})
        # except AttributeError as e:
        #     self.logger.error(e)


if __name__ == "__main__":
    mod = GenerateSEMmontTileSpecs(input_data=example_input)
    mod.run()