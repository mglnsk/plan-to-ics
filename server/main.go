package main

import "github.com/gofiber/fiber/v2"

func main() {
	app := fiber.New()

	app.Get("/", func(c *fiber.Ctx) error {
		// render post form
		return c.SendString("Hello, World!")
	})

	app.Get("/:url", func(c *fiber.Ctx) error {
		u := c.Params("url")

		return c.SendString("Hello, World!")
	})

	app.Listen(":3000")
}
