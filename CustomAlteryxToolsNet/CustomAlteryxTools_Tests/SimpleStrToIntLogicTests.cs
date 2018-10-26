using System;
using NUnit.Framework;
using CustomAlteryxTools;

namespace CustomAlteryxTools_Tests
{
    [TestFixture]
    public class SimpleStrToIntLogicTests
    {
        [Test]
        public void ConvertInvalidString()
        {
            var result = SimpleStrToIntLogic.Convert("10A%0");
            Assert.IsFalse(result.HasValue);
        }

        [Test]
        public void ConvertValidString()
        {
            var result = SimpleStrToIntLogic.Convert("01. -_AB");
            Assert.IsTrue(result.HasValue);
        }

        [Test]
        public void ConvertEmptyString()
        {
            var result = SimpleStrToIntLogic.Convert("");
            Assert.IsFalse(result.HasValue);
        }

        [Test]
        public void ConvertStringTooLong()
        {
            var result = SimpleStrToIntLogic.Convert("ZZZZZZZZZZZZ0");
            Assert.IsFalse(result.HasValue);
        }

        [Test]
        public void Convert0()
        {
            var result = SimpleStrToIntLogic.Convert("0");
            Assert.AreEqual(long.MinValue, result.Value);
        }

        [Test]
        public void ConvertZZZZZZZZZZZZ()
        {
            var result = SimpleStrToIntLogic.Convert("ZZZZZZZZZZZZ");
            Assert.AreEqual(7553843963145224191L, result.Value);
        }

        [Test]
        public void ConvertABC()
        {
            var result = SimpleStrToIntLogic.Convert("ABC");
            Assert.AreEqual(long.MinValue + 23016, result.Value);
        }

        [Test]
        public void LongPowCheck()
        {
            Assert.AreEqual(419430400000000000, SimpleStrToIntLogic.LongPow(40,11));
            Assert.AreEqual(1, SimpleStrToIntLogic.LongPow(40,0));
            Assert.AreEqual(40, SimpleStrToIntLogic.LongPow(40,1));
        }

        [Test]
        public void ConvertNumericString()
        {
            var result = SimpleStrToIntLogic.ConvertNumericOnly("12345");
            Assert.AreEqual(12345, result);

            result = SimpleStrToIntLogic.ConvertNumericOnly("-12345");
            Assert.AreEqual(-12345, result);
            
            result = SimpleStrToIntLogic.ConvertNumericOnly("111111111111111111");
            Assert.AreEqual(111111111111111111, result);
        }

        [Test]
        public void ConvertNumericStringTooLong()
        {
            var result = SimpleStrToIntLogic.ConvertNumericOnly("1111111111111111111111");
            Assert.IsFalse(result.HasValue);
        }

        [Test]
        public void ConvertNumericStringInvalid()
        {
            var result = SimpleStrToIntLogic.ConvertNumericOnly("SDLJ$9DSLKj");
            Assert.IsFalse(result.HasValue);

            result = SimpleStrToIntLogic.ConvertNumericOnly("");
            Assert.IsFalse(result.HasValue);
        }
    }
}