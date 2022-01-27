import math
from xml.dom import minidom
import geojson
import numpy as np
from geojson import Polygon, Feature


# used to store unit name and starting index in file
class Unit:
    def __init__(self, name, ind):
        self.name = name
        self.ind = ind


def limit_array(arr, limit):
    if len(arr) > limit:
        var = math.ceil(len(arr) / limit)
        return arr[::var]
    return arr


def get_value_by_tag(model, tag):
    try:
        return model.getElementsByTagName(tag)[0].firstChild.nodeValue
    except:
        return ""


class GeojsonParser:

    def __init__(self, data_file, out_path, units, limit_num=0, limit_units=[]):
        self.out_path = out_path
        self.limit_num = limit_num
        self.limit_units = limit_units
        self.current_unit = 0
        self.file_data = ""
        self.units = units
        # parse an xml geo_file by name
        geo_file = minidom.parse(data_file)
        self.members = geo_file.getElementsByTagName('base:member')
        self.file_current = None

    def close_previous(self, file):
        file.write("]\n}")
        file.close()

    def open_next(self, name_ind):
        file = open(self.out_path + self.units[name_ind].name + ".json", "w")
        file.write('{\n    "type": "FeatureCollection",\n    "features": [\n')
        return file

    def format_coordinates(self, coord_arr):
        # Switch lat/longt for geojson
        coord_arr = np.array([x[::-1] for x in coord_arr])
        coord_arr = np.append(coord_arr.flatten(), coord_arr[0])
        return Polygon([coord_arr.reshape(int(len(coord_arr) / 2), 2).tolist()])

    def handle_unit_file(self, j, unit):
        if unit.ind != 0:
            self.file_current.write(self.file_data[:-2])
            self.close_previous(self.file_current)
            self.file_data = ""
        self.file_current = self.open_next(j)
        self.current_unit = j

    def parse(self):
        for i, elem in enumerate(self.members):
            # Open and close app. files; Write data to file
            for j, unit in enumerate(self.units):
                if i == unit.ind:
                    self.handle_unit_file(j, unit)

            # Get and format geo data
            geo_data = self.members[i].getElementsByTagName('gml:posList')[0].firstChild.data.split(" ")
            coord_arr = np.array(list(map(float, geo_data))).reshape(int(len(geo_data) / 2), 2)

            # Limit selected units number of coords
            if self.units[self.current_unit].name in self.limit_units:
                coord_arr = limit_array(coord_arr, self.limit_num)

            polygon = self.format_coordinates(coord_arr)

            # Extract properties
            national_code = get_value_by_tag(self.members[i], 'au:nationalCode')
            local_id = get_value_by_tag(self.members[i], 'base:localId')
            identifier = get_value_by_tag(self.members[i], 'identifier')
            name = get_value_by_tag(self.members[i], 'gn:text')

            features = Feature(geometry=polygon, nationalCode=national_code, localId=local_id,
                               id=identifier, name=name)

            self.file_data += geojson.dumps(features)
            self.file_data += ",\n"

        # Write to last file
        self.file_current.write(self.file_data[:-2])
        self.file_current.write("]\n}")


def main():
    file_name = 'data/1.xml'
    file_path_out = "data_parsed/"
    units = [Unit("czech_republic", 0), Unit("kraje", 1), Unit("okresy", 15), Unit("obce", 92),
                      Unit("okresky", 6350)]

    parser = GeojsonParser(file_name, file_path_out, units, 1000, ["obce"])
    parser.parse()


if __name__ == "__main__":
    main()
