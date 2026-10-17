import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
export const Root = () => (
  <Composition id="LunarSouthPole" component={Film} durationInFrames={3540} fps={30} width={1920} height={1080} />
);
