#version 330

uniform mat4 Mvp;

in vec3 in_vert;
in vec3 in_norm;
in vec3 in_color;

out vec3 v_vert;
out vec3 v_norm;
out vec3 v_color;

void main() {
	v_vert = in_vert;
	v_norm = in_norm;
	v_color = in_color;
	gl_Position = Mvp * vec4(v_vert, 1.0);
}
