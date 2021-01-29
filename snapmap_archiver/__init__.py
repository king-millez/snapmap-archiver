import os, sys, argparse
from . import get_data
from .utils import *

def main():
    geo_msg = 'Use comma seperated values for latitude/longitude, e.g: -l="35.0,67.0"'
    parser = argparse.ArgumentParser(description='Download content from Snapmaps', usage='snapmap_archiver -o [OUTPUT DIR] -g="[LATITUDE],[LONGITUDE]"')
    parser.add_argument('-o', dest='output_dir', type=str, help='Output directory for downloaded content.')
    parser.add_argument('-l', '--location', dest='location', type=str, help='Latitude/longitude of desired area.')
    parser.add_argument('-z', dest='zoom_depth', type=float, help='Snapmaps zoom depth, default is 5.')
    parser.add_argument('-r', dest='radius', type=int, help='Maximum Snap radius in meters, default is 10000.')
    parser.add_argument('--write-json', dest='write_json', action='store_true', default=False, help='Write Snap metadata JSON.')
    args = parser.parse_args()

    if(not args.output_dir):
        sys.exit('Output directory (-o) is required.')

    if(not args.location):
        sys.exit('location (-l) is required.')

    if(',' not in args.location):
        sys.exit(geo_msg)

    if(not os.path.isdir(args.output_dir)):
        try:
            os.mkdir(args.output_dir)
        except:
            sys.exit(f'Could not create directory "{args.output_dir}"')

    if(not args.radius):
        args.radius = 10000
    elif(args.radius > 85000):
        print('Supplied radius value is too large (above 85,000). Defaulting to 85000.')
        args.radius = 85000
    
    try:
        geo_data = args.location.split(',', 1)
    except:
        sys.exit(geo_msg)
    api_response = get_data.api_query(float(geo_data[0]), float(geo_data[1]), max_radius=args.radius)
    download_media(args.output_dir, organise_media(api_response), args.write_json)
    
