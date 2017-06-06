#!/bin/sh
# This test does not have the same problem as the llseek test because
# there is no call to open()
cd ../sample_programs > /dev/null;
echo "asdfasdf" > test.txt;
strace -f -s 9999 -vvvvv -o callstat64.strace ./callstat64
cd .. > /dev/null;
OUTPUT=$(python main.py \
       -c "['sample_programs/callstat64']" \
       -t sample_programs/callstat64.strace);
RET=$?
echo $OUTPUT | grep -q "st_size: 9"
FOUND=$?
rm sample_programs/callstat64.strace;
rm sample_programs/test.txt;
cd test > /dev/null;
if [ $RET -ne 0 ] || [ $FOUND -ne 0 ];
   then exit 1
fi
