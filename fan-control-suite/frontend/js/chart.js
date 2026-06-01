class CurveEditor {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.points = [];
    this.dragIndex = -1;
    canvas.addEventListener('mousedown', (e) => this.onDown(e));
    window.addEventListener('mousemove', (e) => this.onMove(e));
    window.addEventListener('mouseup', () => this.dragIndex = -1);
  }

  setPoints(points) {
    this.points = points.map(p => ({ temp: p.temp, pwm: p.pwm }));
    this.draw();
  }

  onDown(e) {
    const {x, y} = this.toLocal(e);
    this.dragIndex = this.points.findIndex(p => {
      const px = this.xOf(p.temp), py = this.yOf(p.pwm);
      return Math.hypot(px - x, py - y) < 10;
    });
  }

  onMove(e) {
    if (this.dragIndex < 0) return;
    const {x, y} = this.toLocal(e);
    const temp = Math.max(20, Math.min(95, Math.round(this.tempOf(x))));
    const pwm = Math.max(0, Math.min(100, Math.round(this.pwmOf(y))));
    this.points[this.dragIndex] = { temp, pwm };
    this.points.sort((a,b) => a.temp - b.temp);
    this.draw();
    if (this.onchange) this.onchange(this.points);
  }

  toLocal(e) {
    const r = this.canvas.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  xOf(temp) { return ((temp - 20) / 75) * this.canvas.width; }
  yOf(pwm) { return this.canvas.height - (pwm / 100) * this.canvas.height; }
  tempOf(x) { return 20 + (x / this.canvas.width) * 75; }
  pwmOf(y) { return ((this.canvas.height - y) / this.canvas.height) * 100; }

  draw() {
    const c = this.ctx, w = this.canvas.width, h = this.canvas.height;
    c.clearRect(0,0,w,h);
    c.strokeStyle = '#d5dce5';
    for (let i = 0; i <= 5; i++) {
      c.beginPath(); c.moveTo(0, i * h / 5); c.lineTo(w, i * h / 5); c.stroke();
    }
    c.strokeStyle = '#1976d2'; c.lineWidth = 2;
    c.beginPath();
    this.points.forEach((p, i) => {
      const x = this.xOf(p.temp), y = this.yOf(p.pwm);
      if (i === 0) c.moveTo(x,y); else c.lineTo(x,y);
    });
    c.stroke();
    c.fillStyle = '#d32f2f';
    this.points.forEach((p) => {
      c.beginPath(); c.arc(this.xOf(p.temp), this.yOf(p.pwm), 5, 0, Math.PI*2); c.fill();
    });
  }
}
