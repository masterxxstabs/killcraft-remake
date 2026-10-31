import { Game } from './game.js';

const game = new Game(document.getElementById('game'));
// Handy for experimenting from the browser console, e.g. game.coins = 9999
window.game = game;
