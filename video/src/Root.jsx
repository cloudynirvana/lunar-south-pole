import React from 'react';
import {Composition} from 'remotion';
import {Film, TOTAL} from './Film';

// TOTAL comes from the scene list, so a scene can be lengthened in one place.
export const Root = () => (
  <Composition id="LunarSouthPole" component={Film} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
);
