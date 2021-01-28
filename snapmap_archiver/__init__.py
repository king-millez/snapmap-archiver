import os, sys, argparse
from . import get_data

def main():
    geo_msg = 'Use comma seperated values for latitude/longitude, e.g: "35.0,67.0"'
    parser = argparse.ArgumentParser(description='Download content from Snapmaps', usage='snapmap_archiver -o [OUTPUT DIR] -g [LATITUDE],[LONGITUDE]')
    parser.add_argument('-o', dest='output_dir', type=str, help='Output directory for downloaded content.')
    parser.add_argument('-g', dest='geolocation', type=str, help='Latitude/longitude of desired area.')
    parser.add_argument('-z', dest='zoom_depth', type=float, help='Snapmaps zoom depth, default is 5.')
    args = parser.parse_args()

    if(not args.output_dir):
        sys.exit('Output directory (-o) is required.')

    if(not args.geolocation):
        sys.exit('Geolocation (-g) is required.')

    if(',' not in args.geolocation):
        sys.exit(geo_msg)

    if(not os.path.isdir(args.output_dir)):
        sys.exit(f'Output directory "{args.output_dir}" does not exist.')

    try:
        geo_data = args.geolocation.split(',', 1)
        print(get_data.api_query(geo_data[0], geo_data[1]))
    except:
        sys.exit(geo_msg)
    
