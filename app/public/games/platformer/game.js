const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const levelOffsetX = 1600;
const levelOffsetY = 900;

const keys = {
  left: false,
  right: false,
  up: false,
  down: false,
  jumpHeld: false
};

const physics = {
  gravity: 0.55,
  moveSpeed: 6.3,
  acceleration: 0.81,
  deceleration: 0.35,
  airDeceleration: 0.08,
  jumpStrength: 11.5,
  jumpCutoff: 4.5,
  jumpBuffer: 4,
  coyoteFrames: 4,
  dashSpeed: 9,
  dashDuration: 15,
  dashStartup: 4,
  dashRefreshWindow: 5,
  dashJumpBoostMultiplier: 1.2,
  dashDownwardBias: 1.2
};

const player = {
  x: levelOffsetX + 80,
  y: levelOffsetY + 290,
  width: 36,
  height: 52,
  velocityX: 0,
  velocityY: 0,
  onGround: false,
  canDash: true,
  facing: 1,
  dashFrames: 0,
  dashMovementFrames: 0,
  dashStartupFrames: 0,
  jumpBufferFrames: 0,
  coyoteFrames: 0
};

const dashTrail = [];

const platforms = [
  { x: levelOffsetX + 0, y: levelOffsetY + 370, width: 800, height: 80 },
  { x: levelOffsetX + 140, y: levelOffsetY + 300, width: 140, height: 18 },
  { x: levelOffsetX + 360, y: levelOffsetY + 245, width: 150, height: 18 },
  { x: levelOffsetX + 590, y: levelOffsetY + 180, width: 120, height: 18 }
];

function drawBackground() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = '#9bd0ff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(levelOffsetX + 90, levelOffsetY + 55, 90, 28);
  ctx.fillRect(levelOffsetX + 118, levelOffsetY + 40, 60, 24);
  ctx.fillRect(levelOffsetX + 470, levelOffsetY + 70, 110, 30);
  ctx.fillRect(levelOffsetX + 505, levelOffsetY + 52, 54, 22);
}

function drawPlatforms() {
  platforms.forEach((platform, index) => {
    ctx.fillStyle = index === 0 ? '#6fb96b' : '#8b5a2b';
    ctx.fillRect(platform.x, platform.y, platform.width, platform.height);

    if (index > 0) {
      ctx.fillStyle = '#c88a4d';
      ctx.fillRect(platform.x, platform.y, platform.width, 6);
    }
  });
}

function drawPlayer() {
  const hasDashColor = !player.canDash;

  ctx.fillStyle = hasDashColor ? '#666666' : '#1f1f1f';
  ctx.fillRect(player.x, player.y, player.width, player.height);

  ctx.fillStyle = hasDashColor ? '#fff8db' : '#f4efe6';
  ctx.fillRect(player.x + 8, player.y + 8, 8, 8);
  ctx.fillRect(player.x + 20, player.y + 8, 8, 8);

  ctx.fillStyle = hasDashColor ? '#ffd166' : '#f97316';
  ctx.fillRect(player.x + 6, player.y + 22, 24, 18);
}

function drawDashTrail() {
  dashTrail.forEach((trailPiece) => {
    ctx.globalAlpha = trailPiece.alpha;

    ctx.fillStyle = '#8d8d8d';
    ctx.fillRect(trailPiece.x, trailPiece.y, player.width, player.height);

    ctx.fillStyle = '#fff8db';
    ctx.fillRect(trailPiece.x + 8, trailPiece.y + 8, 8, 8);
    ctx.fillRect(trailPiece.x + 20, trailPiece.y + 8, 8, 8);

    ctx.fillStyle = '#ffd166';
    ctx.fillRect(trailPiece.x + 6, trailPiece.y + 22, 24, 18);
  });

  ctx.globalAlpha = 1;
}

function drawLabel() {
  ctx.fillStyle = '#1f1f1f';
  ctx.font = '18px sans-serif';
  ctx.fillText('Move: A/D  Jump: Space  Dash: J then aim for 4 frames', 24, 34);
}

function getDashDirection() {
  let dashX = 0;
  let dashY = 0;

  if (keys.left && !keys.right) {
    dashX = -1;
  }

  if (keys.right && !keys.left) {
    dashX = 1;
  }

  if (keys.up && !keys.down) {
    dashY = -1;
  }

  if (keys.down && !keys.up) {
    dashY = 1;
  }

  if (dashX === 0 && dashY === 0) {
    dashX = player.facing;
  }

  // Make repeated downward diagonals shallower than 45 degrees.
  if (dashX !== 0 && dashY > 0) {
    dashY /= physics.dashDownwardBias;
  }

  const length = Math.hypot(dashX, dashY);

  return {
    x: dashX / length,
    y: dashY / length
  };
}

function startJump() {
  player.dashMovementFrames = 0;

  if (player.dashFrames > 0 && Math.abs(player.velocityX) > physics.dashSpeed) {
    const jumpDirection = Math.sign(player.velocityX) || player.facing;

    player.velocityX += jumpDirection * physics.jumpStrength;
    player.velocityY = -(physics.jumpStrength * 0.65);
  } else {
    player.velocityY = -physics.jumpStrength;
  }

  player.onGround = false;
  player.coyoteFrames = 0;
  player.jumpBufferFrames = 0;
}

function handleKeyChange(event, isPressed) {
  if (event.code === 'ArrowLeft' || event.code === 'KeyA') {
    keys.left = isPressed;
  }

  if (event.code === 'ArrowRight' || event.code === 'KeyD') {
    keys.right = isPressed;
  }

  if (event.code === 'ArrowUp' || event.code === 'KeyW') {
    keys.up = isPressed;
  }

  if (event.code === 'ArrowDown' || event.code === 'KeyS') {
    keys.down = isPressed;
  }

  if (event.code === 'Space') {
    if (isPressed && !keys.jumpHeld) {
      keys.jumpHeld = true;
      player.jumpBufferFrames = physics.jumpBuffer;

      if (player.onGround || player.coyoteFrames > 0) {
        startJump();
      }
    }

    if (!isPressed) {
      keys.jumpHeld = false;

      if (player.velocityY < -physics.jumpCutoff) {
        player.velocityY = -physics.jumpCutoff;
      }
    }
  }

  if (event.code === 'KeyJ' && isPressed && player.canDash) {
    player.canDash = false;
    player.dashStartupFrames = physics.dashStartup;
  }
}

function updatePlayer() {
  const wasOnGround = player.onGround;
  const groundedForMovement = player.onGround || player.coyoteFrames > 0;

  if (player.dashStartupFrames > 0) {
    player.dashStartupFrames -= 1;

    if (player.dashStartupFrames === 0) {
      const dashDirection = getDashDirection();
      const currentSpeed = Math.hypot(player.velocityX, player.velocityY);
      const dashLaunchSpeed = Math.max(physics.dashSpeed, currentSpeed);

      player.velocityX = dashDirection.x * dashLaunchSpeed;
      player.velocityY = dashDirection.y * dashLaunchSpeed;
      player.dashFrames = physics.dashDuration;
      player.dashMovementFrames = physics.dashDuration;
    }
  }

  if (player.dashFrames > 0) {
    player.dashFrames -= 1;
  }

  if (player.dashMovementFrames > 0) {
    player.dashMovementFrames -= 1;
    dashTrail.push({
      x: player.x,
      y: player.y,
      alpha: 0.35
    });
  } else {
    if (keys.left && !keys.right) {
      if (!groundedForMovement && player.velocityX <= -physics.moveSpeed) {
        player.velocityX = Math.min(
          -physics.moveSpeed,
          player.velocityX + physics.airDeceleration
        );
      } else {
        player.velocityX -= physics.acceleration;
      }

      player.facing = -1;
    }

    if (keys.right && !keys.left) {
      if (!groundedForMovement && player.velocityX >= physics.moveSpeed) {
        player.velocityX = Math.max(
          physics.moveSpeed,
          player.velocityX - physics.airDeceleration
        );
      } else {
        player.velocityX += physics.acceleration;
      }

      player.facing = 1;
    }

    if (!keys.left && !keys.right) {
      if (player.velocityX > 0) {
        player.velocityX = Math.max(0, player.velocityX - physics.deceleration);
      }

      if (player.velocityX < 0) {
        player.velocityX = Math.min(0, player.velocityX + physics.deceleration);
      }
    }

    if (groundedForMovement) {
      if (player.velocityX > physics.moveSpeed) {
        player.velocityX = Math.max(
          physics.moveSpeed,
          player.velocityX - physics.deceleration
        );
      }

      if (player.velocityX < -physics.moveSpeed) {
        player.velocityX = Math.min(
          -physics.moveSpeed,
          player.velocityX + physics.deceleration
        );
      }

      if (player.velocityX > physics.moveSpeed) {
        player.velocityX = physics.moveSpeed;
      }

      if (player.velocityX < -physics.moveSpeed) {
        player.velocityX = -physics.moveSpeed;
      }
    } else {
      if (player.velocityX > physics.moveSpeed) {
        player.velocityX = Math.max(
          physics.moveSpeed,
          player.velocityX - physics.airDeceleration
        );
      }

      if (player.velocityX < -physics.moveSpeed) {
        player.velocityX = Math.min(
          -physics.moveSpeed,
          player.velocityX + physics.airDeceleration
        );
      }
    }
  }

  dashTrail.forEach((trailPiece) => {
    trailPiece.alpha -= 0.06;
  });

  while (dashTrail.length > 0 && dashTrail[0].alpha <= 0) {
    dashTrail.shift();
  }

  player.x += player.velocityX;

  if (player.x < 0) {
    player.x = 0;
    player.velocityX = 0;
  }

  if (player.x + player.width > canvas.width) {
    player.x = canvas.width - player.width;
    player.velocityX = 0;
  }

  if (player.dashMovementFrames === 0) {
    player.velocityY += physics.gravity;
  }

  player.y += player.velocityY;
  player.onGround = false;

  platforms.forEach((platform) => {
    const playerBottom = player.y + player.height;
    const playerPreviousBottom = playerBottom - player.velocityY;
    const landingVelocityX = player.velocityX;
    const landingVelocityY = player.velocityY;
    const overlappingX =
      player.x + player.width > platform.x &&
      player.x < platform.x + platform.width;
    const fallingOntoPlatform =
      player.velocityY >= 0 &&
      playerBottom >= platform.y &&
      playerPreviousBottom <= platform.y;

    if (overlappingX && fallingOntoPlatform) {
      player.y = platform.y - player.height;
      player.velocityY = 0;
      player.onGround = true;
      player.coyoteFrames = physics.coyoteFrames;

      if (player.dashFrames > 0 && player.dashFrames <= physics.dashRefreshWindow) {
        player.canDash = true;
      }

      if (player.dashFrames > 0 && landingVelocityY > 0 && landingVelocityX !== 0) {
        player.velocityX =
          Math.sign(landingVelocityX) *
          (physics.dashSpeed * physics.dashJumpBoostMultiplier);
      }

      if (!wasOnGround) {
        player.canDash = true;
        player.dashStartupFrames = 0;

        if (player.jumpBufferFrames > 0) {
          startJump();
        }
      }
    }
  });

  if (!player.onGround && wasOnGround) {
    player.coyoteFrames = physics.coyoteFrames;
  }

  if (!player.onGround && player.coyoteFrames > 0) {
    player.coyoteFrames -= 1;
  }

  if (player.y > canvas.height) {
    player.x = levelOffsetX + 80;
    player.y = levelOffsetY + 290;
    player.velocityX = 0;
    player.velocityY = 0;
    player.canDash = true;
    player.dashFrames = 0;
    player.dashMovementFrames = 0;
    player.dashStartupFrames = 0;
    player.jumpBufferFrames = 0;
    player.coyoteFrames = 0;
    dashTrail.length = 0;
  }

  if (player.jumpBufferFrames > 0) {
    player.jumpBufferFrames -= 1;
  }
}

function render() {
  drawBackground();
  drawPlatforms();
  drawDashTrail();
  drawPlayer();
  drawLabel();
}

function gameLoop() {
  updatePlayer();
  render();
  requestAnimationFrame(gameLoop);
}

window.addEventListener('keydown', (event) => {
  if (
    event.code === 'Space' ||
    event.code === 'ArrowUp' ||
    event.code === 'ArrowDown' ||
    event.code === 'ArrowLeft' ||
    event.code === 'ArrowRight'
  ) {
    event.preventDefault();
  }

  handleKeyChange(event, true);
});

window.addEventListener('keyup', (event) => {
  handleKeyChange(event, false);
});

gameLoop();
