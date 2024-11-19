// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.0 <0.9.0;

contract LiteralTest {

    // string-literal
    string constant s = '\u4ee5\u592a' "\x0a'\"\\";

    // number-literal
    uint256 constant n = 0x9e3779b9 * 1000_0000 wei;

    // boolean-literal
    bool constant b = false && true;

    // hex-string-literal
    bytes constant h = hex"9e3779b9";

    // unicode-string-literal
    bytes constant u = unicode"lre‪ rle‫ pdf‬ pdf‬";
}

// interface
interface Interface1 { }
interface Interface2 { }

// (abstract) contract
abstract contract InheritanceTest is Interface1, Interface2 { }

// library
library LibraryTest { }

struct StructTest {
    uint256 member0;
    uint256 member1;
    uint256 member2;
}

enum EnumTest {
    ENUM0,
    ENUM1,
    ENUM2
}

event EventTest1(uint256, uint256, uint256);

error ErrorTest1(uint256, uint256, uint256);