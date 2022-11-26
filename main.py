from io import BufferedWriter
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from os.path import exists
from result import Ok, Err, Result, as_result
import sys
import argparse

class PdfMergeRange:
    
    def __init__(self, _path: str, _start: int = None, _end: int = None) -> None:
        self.path = _path
        self.merge_start = _start
        self.merge_end = _end
    
    path: str
    merge_start: int
    merge_end: int
    
    
class MergeRangeError(Exception):
    
    # def __init__(self, path: str, start: int, end: int, message="Specified a wrong merge range"):
    def __init__(self, pdf_merge_range: PdfMergeRange, message="Specified a wrong merge range"):
        self.pdf_merge_range = pdf_merge_range
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f'{self.message} for path {self.pdf_merge_range.path}: {self.pdf_merge_range.merge_startstart} >= {self.pdf_merge_range.merge_endend}'


@as_result(FileNotFoundError, MergeRangeError)
def merge_pdf(mergers: list[PdfMergeRange]) -> PdfMerger:
    merger = PdfMerger()
    
    for merge_range in mergers:
        
        # Check if path exists
        if(not exists(merge_range.path)):
            raise FileNotFoundError(f"Incorect path to merge file '{merge_range.path}'")
        
        # If no range is specified merge all pages
        if(merge_range.merge_start == None or merge_range.merge_end == None):
            merger.append(merge_range.path)
            
        else:
            # Check if range is correct, start must be lower than end
            if(merge_range.merge_start >= merge_range.merge_end):
                raise MergeRangeError(merge_range)
            
            # Apply page ranges
            merger.append(merge_range.path, pages=(merge_range.merge_start, merge_range.merge_end))

    return merger

@as_result(OSError, IOError)
def write_to_out_pdf(out_path: str):
    writer = PdfWriter()
    buf: BufferedWriter
    
    try:
        buf = open(out_path, "wb")
        writer.write(buf)
    except Exception as e:
        raise e

@as_result(OSError, IOError)
def compress_pdf(path: str):
    reader = PdfReader(path)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
        
    with open(path, "wb") as f: writer.write(f)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog = 'PdfCmd',
                    description = 'A pdf cmd tool to manipulate, fuse and compress pdf files'
                )
    
    parser.add_argument('-f', '--file', type=str, help='a file to treat')
    parser.add_argument('-o', '--outputfile', type=str, help='the output file')
    parser.add_argument('-m', '--merge', type=str, nargs='+', help='the files to merge')
    parser.add_argument('-r', '--ranges', type=int, nargs='+', help='the file ranges to use')
    parser.add_argument('-c', '--compress', action='store_true', help='the file ranges to use')
    
    args = parser.parse_args()
    
    if args.outputfile == None:
        parser.error("Need to specify an output file")
    
    if args.merge != None:      
        if len(args.merge) <= 1:
            parser.error("Need to select at least two files to merge")
            
        mergers: list[PdfMergeRange] = []
            
        if args.ranges is not None:
            if len(args.ranges) != 2 * len(args.merge):
                parser.error("Did not specify all ranges to merge")
            
            j = 0
            for i in  range(0, len(args.merge)):
                mergers.append(PdfMergeRange(args.merge[i], args.ranges[j], args.ranges[j+1]))
                j = j + 2
                
        else:     
            mergers = [PdfMergeRange(p) for p in args.merge]
        
        match merge_pdf(mergers):
            case Ok(merged):
                try:
                    merged.write(args.outputfile)
                    if args.compress == True: compress_pdf(args.outputfile)
                        
                except Exception as e: 
                    sys.exit(e)
                    
            case Err(e): sys.exit(e)
    else:
        parser.print_help()