Iimport sys, argparse
sys.path.append(".")
import source

def main(args):
    source.LTV(
        input_file = args.input_file,
        output_file=args.output_file,
        show_X_customers=args.show_X_customers
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''Run shutterfly LTV calculator'''
    )

    parser.add_argument('input_file', help='file to read data from')
    parser.add_argument('output_file', help='file to save output to')
    parser.add_argument('show_X_customers',  help='total customers to output')
    main(parser.parse_args())