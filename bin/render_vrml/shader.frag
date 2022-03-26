#version 330

uniform vec4 AmbientColor;
uniform vec3 LightDir;

in vec3 v_vert;
in vec3 v_norm;
in vec3 v_color;

out vec4 f_color;

void main() {
	// clip negative fragments (below the board surface level)
	if (v_vert.z < 0.1) {
		discard;
		return;
	}
	// we use abs() to make normals compatible with both CW and CCW faces
	vec3 n = normalize(abs(v_norm));
	// calc luminosity
	float lum = dot(n, LightDir);
	lum = acos(lum) / 3.14159265;
	lum = clamp(lum, 0.0, 1.0);
	lum = lum * lum;
	lum = smoothstep(0.0, 1.0, lum);

	// modulate
	vec3 lcolor = v_color * lum;
	// add ambient color
	vec3 color = lcolor * (1.0 - AmbientColor.a) + AmbientColor.rgb * AmbientColor.a;
	f_color = vec4(color, 1.0);
}
