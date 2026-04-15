// reanimated-mock.js
const React = require('react');

console.log('--- REANIMATED MOCK LOADED ---');

const NOOP = () => {};
const DEFAULT_VALUE = { value: 0 };

const Reanimated = {
  useSharedValue: (v) => ({ value: v }),
  useAnimatedStyle: (fn) => ({}),
  useAnimatedProps: (fn) => ({}),
  useDerivedValue: (fn) => ({ value: fn() }),
  useAnimatedGestureHandler: (handlers) => ({}),
  useAnimatedScrollHandler: (handlers) => ({}),
  useAnimatedRef: () => ({ current: null }),
  useAnimatedReaction: NOOP,
  withTiming: (v, config, cb) => v,
  withSpring: (v, config, cb) => v,
  withSequence: (...args) => args[0],
  withDelay: (d, v) => v,
  withRepeat: (v) => v,
  runOnJS: (fn) => fn,
  runOnUI: (fn) => fn,
  makeMutable: (v) => ({ value: v }),
  interpolate: (v, input, output) => output[0],
  Extrapolation: { CLAMP: 'clamp', IDENTITY: 'identity', EXTEND: 'extend' },
  Easing: {
    linear: NOOP,
    ease: NOOP,
    quad: NOOP,
    cubic: NOOP,
    poly: (n) => NOOP,
    sin: NOOP,
    circle: NOOP,
    exp: NOOP,
    elastic: (b) => NOOP,
    back: (s) => NOOP,
    bounce: NOOP,
    bezier: (x1, y1, x2, y2) => NOOP,
    in: (easing) => NOOP,
    out: (easing) => NOOP,
    inOut: (easing) => NOOP,
  },
  View: 'View',
  Text: 'Text',
  Image: 'Image',
  ScrollView: 'ScrollView',
  createAnimatedComponent: (c) => c,
  addWhitelistedNativeProps: NOOP,
  addWhitelistedUIProps: NOOP,
  Layout: {
    duration: () => ({ duration: () => ({}) }),
    springify: () => ({ springify: () => ({}) }),
  },
  FadeIn: { duration: () => ({}) },
  FadeOut: { duration: () => ({}) },
  SlideInLeft: { duration: () => ({}) },
  SlideOutRight: { duration: () => ({}) },
  // Add more as needed by GiftedChat or KeyboardController
};

module.exports = {
  ...Reanimated,
  default: Reanimated,
};
