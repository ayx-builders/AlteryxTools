using System;
using System.Collections.Generic;
using System.Linq;

namespace CustomAlteryxTools
{
    public static class SimpleStrToIntLogic
    {
        public static long? ConvertNumericOnly(string input)
        {
            if (!long.TryParse(input, out var result))
            {
                return null;
            }
            return result;
        }
        
        public static long? Convert(string input)
        {
            if (input == "") return null;
            if (input.Length > 12) return null;

            var pow = input.Length - 1;
            ulong add = 0;
            foreach (var digit in input)
            {
                if (!_validChars.Contains(digit)) return null;

                add = add + LongPow(40, pow) * _map[digit];
                pow--;
            }

            var add1 = (long)(add / 2);
            var add2 = (long) (add - add / 2);
            return long.MinValue + add1 + add2;
        }

        public static ulong LongPow(long value, int pow)
        {
            var returnValue = (ulong) value;
            
            if (pow == 0) return 1;
            var multiplier = returnValue;
            for (var i = 1; i < pow; i++)
            {
                returnValue = returnValue * multiplier;
            }

            return returnValue;
        }
        
        private static Dictionary<char, ulong> _map = new Dictionary<char, ulong>
        {
            { '0', 0 },
            { '1', 1 },
            { '2', 2 },
            { '3', 3 },
            { '4', 4 },
            { '5', 5 },
            { '6', 6 },
            { '7', 7 },
            { '8', 8 },
            { '9', 9 },
            { ' ', 10 },
            { '_', 11 },
            { '-', 12 },
            { '.', 13 },
            { 'A', 14 },
            { 'B', 15 },
            { 'C', 16 },
            { 'D', 17 },
            { 'E', 18 },
            { 'F', 19 },
            { 'G', 20 },
            { 'H', 21 },
            { 'I', 22 },
            { 'J', 23 },
            { 'K', 24 },
            { 'L', 25 },
            { 'M', 26 },
            { 'N', 27 },
            { 'O', 28 },
            { 'P', 29 },
            { 'Q', 30 },
            { 'R', 31 },
            { 'S', 32 },
            { 'T', 33 },
            { 'U', 34 },
            { 'V', 35 },
            { 'W', 36 },
            { 'X', 37 },
            { 'Y', 38 },
            { 'Z', 39 }
        };

        private static char[] _validChars =
        {
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', '_', '-', '.', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
            'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
        };
    }
}