// All sounds are synthesised on the fly, so the game needs no audio files.
export class Audio {
  constructor() {
    this.ctx = null;
    this.volume = 0.5;
    this.muted = false;
  }

  unlock() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      this.ctx = new AC();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
      this.noiseBuf = this.ctx.createBuffer(1, this.ctx.sampleRate, this.ctx.sampleRate);
      const d = this.noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    if (this.ctx.state === 'suspended') this.ctx.resume();
  }

  setVolume(v) {
    this.volume = v;
    if (this.master) this.master.gain.value = this.muted ? 0 : v;
  }

  toggleMute() {
    this.muted = !this.muted;
    this.setVolume(this.volume);
    return this.muted;
  }

  get ok() { return this.ctx && !this.muted; }

  noise(dur, { freq = 1000, q = 1, type = 'lowpass', vol = 0.5, attack = 0.002, sweep } = {}) {
    if (!this.ok) return;
    const t = this.ctx.currentTime;
    const src = this.ctx.createBufferSource();
    src.buffer = this.noiseBuf;
    src.playbackRate.value = 0.5 + Math.random();
    const f = this.ctx.createBiquadFilter();
    f.type = type; f.frequency.setValueAtTime(freq, t); f.Q.value = q;
    if (sweep) f.frequency.exponentialRampToValueAtTime(sweep, t + dur);
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f).connect(g).connect(this.master);
    src.start(t, Math.random() * 0.5);
    src.stop(t + dur + 0.05);
  }

  tone(freq, dur, { type = 'square', vol = 0.2, to, delay = 0 } = {}) {
    if (!this.ok) return;
    const t = this.ctx.currentTime + delay;
    const o = this.ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (to) o.frequency.exponentialRampToValueAtTime(to, t + dur);
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(this.master);
    o.start(t);
    o.stop(t + dur + 0.05);
  }

  shoot(id) {
    switch (id) {
      case 'pistol': this.noise(0.12, { freq: 2200, vol: 0.5, sweep: 400 }); this.tone(180, 0.08, { vol: 0.15, to: 60 }); break;
      case 'nailgun': this.noise(0.06, { freq: 3500, type: 'bandpass', q: 2, vol: 0.4 }); this.tone(900, 0.04, { vol: 0.06, to: 400 }); break;
      case 'scatter': this.noise(0.3, { freq: 1400, vol: 0.8, sweep: 150 }); this.tone(90, 0.2, { vol: 0.3, to: 40 }); break;
      case 'railspike': this.tone(1800, 0.35, { type: 'sawtooth', vol: 0.15, to: 120 }); this.noise(0.25, { freq: 5000, type: 'highpass', vol: 0.3 }); break;
      case 'firework': this.noise(0.4, { freq: 800, type: 'bandpass', vol: 0.5, sweep: 3000 }); break;
      default: this.noise(0.1, { freq: 1500, vol: 0.4 });
    }
  }

  swing() { this.noise(0.15, { freq: 600, type: 'bandpass', q: 1.5, vol: 0.25, sweep: 1800, attack: 0.03 }); }
  hit() { this.tone(520, 0.05, { vol: 0.12, to: 300 }); }
  headshot() { this.tone(1200, 0.08, { vol: 0.15, to: 1600 }); }
  thud() { this.noise(0.08, { freq: 400, vol: 0.4 }); }
  reload() { this.tone(300, 0.05, { vol: 0.1 }); this.tone(500, 0.05, { vol: 0.1, delay: 0.12 }); }
  empty() { this.tone(1400, 0.03, { vol: 0.08 }); }
  hurt() { this.tone(160, 0.18, { type: 'sawtooth', vol: 0.18, to: 80 }); }
  coin() { this.tone(988, 0.06, { vol: 0.08 }); this.tone(1319, 0.12, { vol: 0.08, delay: 0.06 }); }
  heal() { this.tone(523, 0.1, { type: 'sine', vol: 0.15 }); this.tone(784, 0.15, { type: 'sine', vol: 0.15, delay: 0.08 }); }
  buy() { this.tone(660, 0.08, { vol: 0.12 }); this.tone(880, 0.08, { vol: 0.12, delay: 0.08 }); this.tone(1320, 0.12, { vol: 0.12, delay: 0.16 }); }
  deny() { this.tone(200, 0.15, { vol: 0.12 }); }
  groan() { this.tone(90 + Math.random() * 60, 0.5, { type: 'sawtooth', vol: 0.05, to: 60 }); }
  spit() { this.noise(0.2, { freq: 900, type: 'bandpass', q: 4, vol: 0.25, sweep: 300 }); }
  boom(v = 1) { this.noise(0.9, { freq: 900, vol: 0.9 * v, sweep: 60 }); this.tone(70, 0.6, { type: 'sine', vol: 0.5 * v, to: 30 }); }
  powerup() { [440, 554, 659, 880].forEach((f, i) => this.tone(f, 0.12, { vol: 0.1, delay: i * 0.06 })); }
  blink() { this.tone(300, 0.2, { type: 'sine', vol: 0.15, to: 1500 }); }
  death() { this.tone(200, 0.25, { type: 'square', vol: 0.06, to: 60 }); }
  waveStart() { this.tone(220, 0.6, { type: 'sawtooth', vol: 0.12 }); this.tone(330, 0.6, { type: 'sawtooth', vol: 0.08, delay: 0.25 }); }
  waveClear() { [523, 659, 784, 1046].forEach((f, i) => this.tone(f, 0.25, { type: 'triangle', vol: 0.15, delay: i * 0.1 })); }
  bossRoar() { this.tone(70, 1.4, { type: 'sawtooth', vol: 0.3, to: 40 }); this.noise(1.2, { freq: 300, vol: 0.4 }); }
  gameOver() { [392, 330, 262, 196].forEach((f, i) => this.tone(f, 0.4, { type: 'triangle', vol: 0.15, delay: i * 0.25 })); }
}
