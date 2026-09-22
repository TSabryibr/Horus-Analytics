import '@testing-library/jest-dom';
import { TextEncoder as NodeTextEncoder, TextDecoder as NodeTextDecoder } from 'node:util';

if (typeof global.TextEncoder === 'undefined') {
    global.TextEncoder = NodeTextEncoder;
    global.TextDecoder = NodeTextDecoder as unknown as typeof TextDecoder;
}

if (typeof URL.createObjectURL === 'undefined') {
    URL.createObjectURL = () => 'blob:test';
    URL.revokeObjectURL = () => {};
}
