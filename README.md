# VIPNT
Python 2.x library for reading and parsing VIPNT inkjet files. 

VIPNT is an inkjet controller file format used by commercial printers to drive fixed inkjet printing heads over a moving substrate.  Typically used to print mail and address data on to letters and magazines.  It dates back to the 80's when physical tapes had to been shipped to your printer containing your mailing lists.  In those days, a reel tape help 140MB and a cartidge held 200MB.  The VIPNT format was a variable width format utilizing the non-printing ASCII characters \x1d-Group Separator, \x1e-Record Separator, and \x1f-Unit Separator.  By using the ASCII defined delimeters the problems typically associated with CSV files are avoided.  (J. Johnah Jameson, III   and Daily Planet, Inc.  are typically problematic)

I wrote this class back when I was in the mailing industry and needed to trouble shoot issues in production.  The most troubling aspect of this format, is that a Record Separator occurs at the start of a record and the files typically did not contain any line breaks.

I realese this to the world for the next unfortunate soul who has to deal with this format.
