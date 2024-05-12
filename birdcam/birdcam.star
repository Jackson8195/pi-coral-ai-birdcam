load("render.star", "render")
load("encoding/base64.star", "base64")
load("http.star", "http")

PIXEL_MONSTER = http.get("https://app.pixelencounter.com/api/basic/monsters/random/png?size=100").body()

def main():
    return render.Root(
        child = render.Box(
            render.Column(
                expanded = True,
                main_align = "space_evenly",
                cross_align = "center",
                children = [
                    render.Image(src = PIXEL_MONSTER, height = 100),
                ],
            )
        )
    )
