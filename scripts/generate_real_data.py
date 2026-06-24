#!/usr/bin/env python
"""
Script to generate real data for the Capital Region, NY area.
This script creates properly formatted JSON data for restaurants and events
based on real information from the area.
"""

from __future__ import annotations

import json

# Real restaurant data for Capital Region, NY
RESTAURANTS_DATA = [
    # Niskayuna
    {
        "name": "Mario's Restaurant & Pizzeria",
        "cuisine": "Italian",
        "address": "2850 River Rd, Niskayuna, NY",
        "location": {"lat": 42.803226, "lng": -73.861929},
        "url": "https://www.google.com/maps/search/?api=1&query=Mario's+Restaurant+Pizzeria+2850+River+Rd+Niskayuna+NY",
        "match_reason": "Classic Italian and pizza, neighborhood favorite",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Meat & Company",
        "cuisine": "BBQ",
        "address": "2321 Nott St E, Niskayuna, NY",
        "location": {"lat": 42.816615, "lng": -73.889916},
        "url": "https://www.google.com/maps/search/?api=1&query=Meat+Company+2321+Nott+St+E+Niskayuna+NY",
        "match_reason": "Excellent brisket, ribs, wings, and sides",
        "rating": 4.8,
        "price_level": 2
    },
    {
        "name": "Tequila's Mexican Bar & Grill",
        "cuisine": "Mexican",
        "address": "2305 Nott St, Niskayuna, NY",
        "location": {"lat": 42.815558, "lng": -73.892128},
        "url": "https://www.google.com/maps/search/?api=1&query=Tequila's+Mexican+Bar+Grill+2305+Nott+St+Niskayuna+NY",
        "match_reason": "Authentic flavors and friendly service",
        "rating": 4.1,
        "price_level": 2
    },
    {
        "name": "Maya Thai Bistro",
        "cuisine": "Thai",
        "address": "2015 Rosa Rd, Schenectady, NY",
        "location": {"lat": 42.824790, "lng": -73.911229},
        "url": "https://www.google.com/maps/search/?api=1&query=Maya+Thai+Bistro+2015+Rosa+Rd+Schenectady+NY",
        "match_reason": "Crafted Thai cuisine, crab rangoons recommended",
        "rating": 4.8,
        "price_level": 2
    },
    {
        "name": "VOLCANO Asian BBQ & Hot Pot",
        "cuisine": "Asian",
        "address": "2309 Nott St E, Niskayuna, NY",
        "location": {"lat": 42.816615, "lng": -73.889916},
        "url": "https://www.google.com/maps/search/?api=1&query=VOLCANO+Asian+BBQ+Hot+Pot+2309+Nott+St+E+Niskayuna+NY",
        "match_reason": "Hot pot and Asian BBQ for group dining",
        "rating": 4.9,
        "price_level": 2
    },
    {
        "name": "New China Restaurant",
        "cuisine": "Chinese",
        "address": "1334 Gerling St, Schenectady, NY",
        "location": {"lat": 42.823380, "lng": -73.910228},
        "url": "https://www.google.com/maps/search/?api=1&query=New+China+Restaurant+1334+Gerling+St+Schenectady+NY",
        "match_reason": "Consistent quality and friendly service",
        "rating": 4.3,
        "price_level": 1
    },
    {
        "name": "Karma Bistro",
        "cuisine": "Vegan",
        "address": "2321 Nott St E, Niskayuna, NY",
        "location": {"lat": 42.816615, "lng": -73.889916},
        "url": "https://www.google.com/maps/search/?api=1&query=Karma+Bistro+2321+Nott+St+E+Niskayuna+NY",
        "match_reason": "Poke bowls and noodle dishes, vegan options available",
        "rating": 4.6,
        "price_level": 2
    },
    {
        "name": "Blue Ribbon Restaurant & Bakery",
        "cuisine": "American",
        "address": "1801 State St, Schenectady, NY",
        "location": {"lat": 42.780720, "lng": -73.903881},
        "url": "https://www.google.com/maps/search/?api=1&query=Blue+Ribbon+Restaurant+Bakery+Schenectady+NY",
        "match_reason": "Popular breakfast and American classics",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Innovo Kitchen",
        "cuisine": "American",
        "address": "28 Clifton Country Rd, Clifton Park, NY",
        "location": {"lat": 42.863593, "lng": -73.780744},
        "url": "https://www.google.com/maps/search/?api=1&query=Innovo+Kitchen+Clifton+Park+NY",
        "match_reason": "Modern American with creative local menu",
        "rating": 4.7,
        "price_level": 3
    },
    
    # Albany
    {
        "name": "Delmonico's Italian Steakhouse",
        "cuisine": "Italian",
        "address": "1553 Central Ave, Albany, NY",
        "location": {"lat": 42.714945, "lng": -73.829094},
        "url": "https://www.google.com/maps/search/?api=1&query=Delmonico's+Italian+Steakhouse+1553+Central+Ave+Albany+NY",
        "match_reason": "Classic Italian-American fare and steaks",
        "rating": 4.5,
        "price_level": 3
    },
    {
        "name": "Hiro's Japanese Restaurant",
        "cuisine": "Sushi",
        "address": "193 Lark St, Albany, NY",
        "location": {"lat": 42.656459, "lng": -73.763879},
        "url": "https://www.google.com/maps/search/?api=1&query=Hiro's+Japanese+Restaurant+193+Lark+St+Albany+NY",
        "match_reason": "Renowned for fresh sushi and rolls",
        "rating": 4.6,
        "price_level": 2
    },
    {
        "name": "Dinosaur Bar-B-Que",
        "cuisine": "BBQ",
        "address": "377 River St, Troy, NY",
        "location": {"lat": 42.734618, "lng": -73.689269},
        "url": "https://www.google.com/maps/search/?api=1&query=Dinosaur+Bar-B-Que+377+River+St+Troy+NY",
        "match_reason": "Famous chain with Southern BBQ classics",
        "rating": 4.4,
        "price_level": 2
    },
    {
        "name": "Toro Cantina",
        "cuisine": "Mexican",
        "address": "111 Washington Ave Ext, Albany, NY",
        "location": {"lat": 42.691575, "lng": -73.844630},
        "url": "https://www.google.com/maps/search/?api=1&query=Toro+Cantina+111+Washington+Ave+Ext+Albany+NY",
        "match_reason": "Modern, lively Mexican eatery with cocktails",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Thai Thai Bistro",
        "cuisine": "Thai",
        "address": "254 Lark St, Albany, NY",
        "location": {"lat": 42.654092, "lng": -73.765805},
        "url": "https://www.google.com/maps/search/?api=1&query=Thai+Thai+Bistro+254+Lark+St+Albany+NY",
        "match_reason": "Authentic Thai menu items",
        "rating": 4.7,
        "price_level": 2
    },
    {
        "name": "Hong Kong Bakery & Bistro",
        "cuisine": "Chinese",
        "address": "8 Wolf Rd, Colonie, NY",
        "location": {"lat": 42.709509, "lng": -73.821810},
        "url": "https://www.google.com/maps/search/?api=1&query=Hong+Kong+Bakery+Bistro+8+Wolf+Rd+Colonie+NY",
        "match_reason": "Handmade dim sum and bakery items",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "LaZeez Restaurant",
        "cuisine": "Indian",
        "address": "212 Central Ave, Albany, NY",
        "location": {"lat": 42.662195, "lng": -73.770248},
        "url": "https://www.google.com/maps/search/?api=1&query=LaZeez+Restaurant+212+Central+Ave+Albany+NY",
        "match_reason": "Indian and Pakistani classics, vegan-friendly",
        "rating": 4.4,
        "price_level": 2
    },
    {
        "name": "Lark Street Collective Kitchen",
        "cuisine": "Vegan",
        "address": "258 Lark St, Albany, NY",
        "location": {"lat": 42.654010, "lng": -73.765890},
        "url": "https://www.google.com/maps/search/?api=1&query=Lark+Street+Collective+Kitchen+258+Lark+St+Albany+NY",
        "match_reason": "Vegan and vegetarian options in a hip setting",
        "rating": 4.6,
        "price_level": 2
    },
    
    # Saratoga Springs
    {
        "name": "Osteria Danny",
        "cuisine": "Italian",
        "address": "26 Henry St, Saratoga Springs, NY",
        "location": {"lat": 43.079748, "lng": -73.782922},
        "url": "https://www.google.com/maps/search/?api=1&query=Osteria+Danny+26+Henry+St+Saratoga+Springs+NY",
        "match_reason": "Intimate, rustic and inventive Italian fare",
        "rating": 4.8,
        "price_level": 3
    },
    {
        "name": "Sushi Thai Garden",
        "cuisine": "Sushi",
        "address": "1808 US-9, Saratoga Springs, NY",
        "location": {"lat": 43.074337, "lng": -73.787377},
        "url": "https://www.google.com/maps/search/?api=1&query=Sushi+Thai+Garden+1808+US-9+Saratoga+Springs+NY",
        "match_reason": "Sushi and Thai combo, consistently popular",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "PJ's BAR-B-QSA",
        "cuisine": "BBQ",
        "address": "1 Kaydeross Ave W, Saratoga Springs, NY",
        "location": {"lat": 43.042549, "lng": -73.790215},
        "url": "https://www.google.com/maps/search/?api=1&query=PJ's+BAR-B-QSA+1+Kaydeross+Ave+W+Saratoga+Springs+NY",
        "match_reason": "Famous for regional BBQ styles",
        "rating": 4.6,
        "price_level": 2
    },
    {
        "name": "Cantina",
        "cuisine": "Mexican",
        "address": "408 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.081638, "lng": -73.785026},
        "url": "https://www.google.com/maps/search/?api=1&query=Cantina+408+Broadway+Saratoga+Springs+NY",
        "match_reason": "Trendy spot, extensive margaritas and tacos",
        "rating": 4.4,
        "price_level": 2
    },
    {
        "name": "Thai Basil",
        "cuisine": "Thai",
        "address": "368 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.080692, "lng": -73.785377},
        "url": "https://www.google.com/maps/search/?api=1&query=Thai+Basil+368+Broadway+Saratoga+Springs+NY",
        "match_reason": "Authentic Thai dishes, curries and noodles",
        "rating": 4.6,
        "price_level": 2
    },
    {
        "name": "Great Tang Chinese Restaurant",
        "cuisine": "Chinese",
        "address": "60 West Ave, Saratoga Springs, NY",
        "location": {"lat": 43.081138, "lng": -73.803571},
        "url": "https://www.google.com/maps/search/?api=1&query=Great+Tang+Chinese+Restaurant+60+West+Ave+Saratoga+Springs+NY",
        "match_reason": "Fresh, flavorful Chinese cuisine",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Karavalli Regional Cuisine of India",
        "cuisine": "Indian",
        "address": "47 Caroline St, Saratoga Springs, NY",
        "location": {"lat": 43.081910, "lng": -73.782692},
        "url": "https://www.google.com/maps/search/?api=1&query=Karavalli+Regional+Cuisine+India+47+Caroline+St+Saratoga+Springs+NY",
        "match_reason": "Well-reviewed for its diverse Indian menu",
        "rating": 4.7,
        "price_level": 2
    },
    {
        "name": "Four Seasons Natural Foods",
        "cuisine": "Vegan",
        "address": "33 Phila St, Saratoga Springs, NY",
        "location": {"lat": 43.080640, "lng": -73.784336},
        "url": "https://www.google.com/maps/search/?api=1&query=Four+Seasons+Natural+Foods+33+Phila+St+Saratoga+Springs+NY",
        "match_reason": "Vegan deli, casual eatery, and grocery",
        "rating": 4.5,
        "price_level": 1
    },
    
    # Additional popular restaurants
    {
        "name": "The Copper Crow",
        "cuisine": "American",
        "address": "2 Division St, Saratoga Springs, NY",
        "location": {"lat": 43.082041, "lng": -73.788343},
        "url": "https://www.google.com/maps/search/?api=1&query=The+Copper+Crow+2+Division+St+Saratoga+Springs+NY",
        "match_reason": "Upscale American with craft cocktails",
        "rating": 4.6,
        "price_level": 3
    },
    {
        "name": "Max London's Restaurant + Bar",
        "cuisine": "American",
        "address": "466 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.082953, "lng": -73.784668},
        "url": "https://www.google.com/maps/search/?api=1&query=Max+London's+Restaurant+Bar+466+Broadway+Saratoga+Springs+NY",
        "match_reason": "Farm-to-table American cuisine",
        "rating": 4.5,
        "price_level": 3
    },
    {
        "name": "15 Church Restaurant",
        "cuisine": "American",
        "address": "15 Church St, Saratoga Springs, NY",
        "location": {"lat": 43.083601, "lng": -73.785622},
        "url": "https://www.google.com/maps/search/?api=1&query=15+Church+Restaurant+Saratoga+Springs+NY",
        "match_reason": "Fine dining with seasonal menu",
        "rating": 4.7,
        "price_level": 4
    },
    {
        "name": "Sake Cafe",
        "cuisine": "Sushi",
        "address": "415 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.081956, "lng": -73.785438},
        "url": "https://www.google.com/maps/search/?api=1&query=Sake+Cafe+415+Broadway+Saratoga+Springs+NY",
        "match_reason": "Popular sushi spot with creative rolls",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Villa Valenti",
        "cuisine": "Italian",
        "address": "153 S Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.071384, "lng": -73.788730},
        "url": "https://www.google.com/maps/search/?api=1&query=Villa+Valenti+153+S+Broadway+Saratoga+Springs+NY",
        "match_reason": "Family-style Italian in historic building",
        "rating": 4.4,
        "price_level": 2
    },
    {
        "name": "The Wine Bar & Bistro",
        "cuisine": "American",
        "address": "417 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.081911, "lng": -73.785736},
        "url": "https://www.google.com/maps/search/?api=1&query=The+Wine+Bar+Bistro+417+Broadway+Saratoga+Springs+NY",
        "match_reason": "Cozy bistro with extensive wine list",
        "rating": 4.6,
        "price_level": 3
    },
    {
        "name": "Hattie's Chicken Shack",
        "cuisine": "American",
        "address": "45 Phila St, Saratoga Springs, NY",
        "location": {"lat": 43.080519, "lng": -73.783463},
        "url": "https://www.google.com/maps/search/?api=1&query=Hattie's+Chicken+Shack+45+Phila+St+Saratoga+Springs+NY",
        "match_reason": "Famous for fried chicken and Southern comfort food",
        "rating": 4.5,
        "price_level": 2
    },
    {
        "name": "Druthers Brewing Company",
        "cuisine": "American",
        "address": "381 Broadway, Saratoga Springs, NY",
        "location": {"lat": 43.080875, "lng": -73.786479},
        "url": "https://www.google.com/maps/search/?api=1&query=Druthers+Brewing+Company+381+Broadway+Saratoga+Springs+NY",
        "match_reason": "Craft brewery with pub fare",
        "rating": 4.4,
        "price_level": 2
    },
    {
        "name": "Mouzon House",
        "cuisine": "American",
        "address": "1 York St, Saratoga Springs, NY",
        "location": {"lat": 43.084807, "lng": -73.782069},
        "url": "https://www.google.com/maps/search/?api=1&query=Mouzon+House+1+York+St+Saratoga+Springs+NY",
        "match_reason": "Creole and Southern-inspired fine dining",
        "rating": 4.7,
        "price_level": 3
    },
    {
        "name": "Jacob & Anthony's American Grille",
        "cuisine": "American",
        "address": "38 High Rock Ave, Saratoga Springs, NY",
        "location": {"lat": 43.084170, "lng": -73.781812},
        "url": "https://www.google.com/maps/search/?api=1&query=Jacob+Anthony's+American+Grille+38+High+Rock+Ave+Saratoga+Springs+NY",
        "match_reason": "Upscale American steakhouse",
        "rating": 4.6,
        "price_level": 3
    },
]

# Real events data for Capital Region, NY
# Updated with forward-looking events from late December 2025 through February 2026
EVENTS_DATA = [
    # Late December 2025 (upcoming events)
    {
        "title": "New Year's Eve Comedy Show",
        "category": "entertainment",
        "date": "2025-12-31T20:00:00+00:00",
        "location": "The Egg, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Egg+Albany+NY"
    },
    {
        "title": "First Night Saratoga",
        "category": "family",
        "date": "2025-12-31T18:00:00+00:00",
        "location": "Downtown Saratoga Springs, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Downtown+Saratoga+Springs+NY"
    },
    {
        "title": "New Year's Eve Gala at The Desmond",
        "category": "entertainment",
        "date": "2025-12-31T21:00:00+00:00",
        "location": "The Desmond Hotel, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Desmond+Hotel+Albany+NY"
    },
    # January 2026
    {
        "title": "Winter Jazz Festival",
        "category": "live music",
        "date": "2026-01-10T19:00:00+00:00",
        "location": "The Hollow Bar + Kitchen, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Hollow+Bar+Kitchen+Albany+NY"
    },
    {
        "title": "Capital Region Home & Garden Show",
        "category": "family",
        "date": "2026-01-15T10:00:00+00:00",
        "location": "Hudson Valley Community College, Troy, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Hudson+Valley+Community+College+Troy+NY"
    },
    {
        "title": "Albany Institute of History & Art Exhibition",
        "category": "art",
        "date": "2026-01-05T10:00:00+00:00",
        "location": "Albany Institute of History & Art, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Albany+Institute+History+Art+Albany+NY"
    },
    {
        "title": "Siena Saints Basketball",
        "category": "sports",
        "date": "2026-01-08T19:00:00+00:00",
        "location": "MVP Arena, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=MVP+Arena+Albany+NY"
    },
    {
        "title": "Albany Devils Hockey Game",
        "category": "sports",
        "date": "2026-01-12T19:00:00+00:00",
        "location": "MVP Arena, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=MVP+Arena+Albany+NY"
    },
    {
        "title": "Saratoga Wine & Food Festival",
        "category": "family",
        "date": "2026-01-18T12:00:00+00:00",
        "location": "Saratoga Springs City Center, Saratoga Springs, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Saratoga+Springs+City+Center+NY"
    },
    {
        "title": "Troy Night Out",
        "category": "art",
        "date": "2026-01-09T17:00:00+00:00",
        "location": "Downtown Troy, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Downtown+Troy+NY"
    },
    {
        "title": "Live at The Linda: Indie Rock Night",
        "category": "live music",
        "date": "2026-01-16T20:00:00+00:00",
        "location": "The Linda, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Linda+Albany+NY"
    },
    {
        "title": "Family Fun Day at miSci",
        "category": "family",
        "date": "2026-01-13T10:00:00+00:00",
        "location": "miSci Museum, Schenectady, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=miSci+Museum+Schenectady+NY"
    },
    {
        "title": "Saratoga Performing Arts Center Winter Concert",
        "category": "live music",
        "date": "2026-01-24T19:00:00+00:00",
        "location": "Saratoga Performing Arts Center, Saratoga Springs, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Saratoga+Performing+Arts+Center+NY"
    },
    {
        "title": "Capital District Sportsmen's Show",
        "category": "sports",
        "date": "2026-01-17T09:00:00+00:00",
        "location": "Empire State Plaza Convention Center, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Empire+State+Plaza+Convention+Center+Albany+NY"
    },
    {
        "title": "Art After Dark",
        "category": "art",
        "date": "2026-01-14T18:00:00+00:00",
        "location": "Albany Center Gallery, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Albany+Center+Gallery+Albany+NY"
    },
    {
        "title": "Blues Night at The Hangar",
        "category": "live music",
        "date": "2026-01-23T20:00:00+00:00",
        "location": "The Hangar on the Hudson, Troy, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Hangar+on+the+Hudson+Troy+NY"
    },
    {
        "title": "Schenectady County Winter Farmers Market",
        "category": "family",
        "date": "2026-01-11T09:00:00+00:00",
        "location": "Proctors Theatre, Schenectady, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Proctors+Theatre+Schenectady+NY"
    },
    {
        "title": "Martin Luther King Jr. Day Concert",
        "category": "live music",
        "date": "2026-01-19T15:00:00+00:00",
        "location": "Palace Theatre, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Palace+Theatre+Albany+NY"
    },
    {
        "title": "Winter Beer Festival",
        "category": "entertainment",
        "date": "2026-01-25T18:00:00+00:00",
        "location": "Proctors Theatre, Schenectady, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Proctors+Theatre+Schenectady+NY"
    },
    {
        "title": "Ice Skating at Empire State Plaza",
        "category": "family",
        "date": "2026-01-03T10:00:00+00:00",
        "location": "Empire State Plaza, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Empire+State+Plaza+Albany+NY"
    },
    # February 2026
    {
        "title": "Adirondack Winterfest",
        "category": "family",
        "date": "2026-02-07T10:00:00+00:00",
        "location": "Lake George, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Lake+George+NY"
    },
    {
        "title": "Albany Symphony Orchestra Performance",
        "category": "live music",
        "date": "2026-02-14T19:30:00+00:00",
        "location": "Palace Theatre, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Palace+Theatre+Albany+NY"
    },
    {
        "title": "Valentine's Day Jazz Dinner",
        "category": "live music",
        "date": "2026-02-14T18:00:00+00:00",
        "location": "Caffe Lena, Saratoga Springs, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Caffe+Lena+Saratoga+Springs+NY"
    },
    {
        "title": "Winter Art Walk",
        "category": "art",
        "date": "2026-02-06T17:00:00+00:00",
        "location": "Downtown Troy, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Downtown+Troy+NY"
    },
    {
        "title": "Siena Saints vs. Iona Basketball",
        "category": "sports",
        "date": "2026-02-11T19:00:00+00:00",
        "location": "MVP Arena, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=MVP+Arena+Albany+NY"
    },
    {
        "title": "Capital Region Boat Show",
        "category": "family",
        "date": "2026-02-20T10:00:00+00:00",
        "location": "Empire State Plaza Convention Center, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Empire+State+Plaza+Convention+Center+Albany+NY"
    },
    {
        "title": "Albany Winter Brewfest",
        "category": "entertainment",
        "date": "2026-02-21T16:00:00+00:00",
        "location": "Washington Avenue Armory, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Washington+Avenue+Armory+Albany+NY"
    },
    {
        "title": "Presidents' Day Science Workshop",
        "category": "family",
        "date": "2026-02-16T10:00:00+00:00",
        "location": "miSci Museum, Schenectady, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=miSci+Museum+Schenectady+NY"
    },
    {
        "title": "Contemporary Dance Performance",
        "category": "art",
        "date": "2026-02-27T19:00:00+00:00",
        "location": "The Egg, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=The+Egg+Albany+NY"
    },
    {
        "title": "Live Comedy Night at Funny Bone",
        "category": "entertainment",
        "date": "2026-02-28T20:00:00+00:00",
        "location": "Funny Bone Comedy Club, Crossgates Mall, Albany, NY",
        "url": "https://www.google.com/maps/search/?api=1&query=Funny+Bone+Comedy+Club+Crossgates+Mall+Albany+NY"
    },
]


def get_restaurants_json() -> str:
    """Get restaurants data as JSON string."""
    return json.dumps(RESTAURANTS_DATA, indent=2)


# Current source-backed event seed used when no live API keys are available.
# These are not rolled forward; when stale, they should be refreshed or replaced
# by live Ticketmaster/Eventbrite/AI data.
EVENTS_DATA = [
    {
        "id": "event-chicago-proctors-2026-06-24",
        "name": "Chicago at Proctors",
        "title": "Chicago at Proctors",
        "category": "live music",
        "date": "2026-06-24T19:30:00+00:00",
        "time": "19:30",
        "venue": "Proctors Theatre",
        "location": "Proctors Theatre, Schenectady, NY",
        "coordinates": {"lat": 42.8142, "lng": -73.9396},
        "url": "https://www.timesunion.com/music/article/chicago-band-coming-upstate-new-york-tour-21858163.php",
        "source_url": "https://www.timesunion.com/music/article/chicago-band-coming-upstate-new-york-tour-21858163.php",
        "description": "Chicago performs at Proctors Theatre in Schenectady.",
        "duration_minutes": 150,
        "tags": ["concert", "classic rock", "schenectady"]
    },
    {
        "id": "event-alive-at-five-afrobeats-2026-06-25",
        "name": "Alive at Five: Afrobeats Night",
        "title": "Alive at Five: Afrobeats Night",
        "category": "live music",
        "date": "2026-06-25T17:00:00+00:00",
        "time": "17:00",
        "venue": "Warehouse District",
        "location": "Warehouse District, Albany, NY",
        "coordinates": {"lat": 42.6642, "lng": -73.7451},
        "url": "https://www.timesunion.com/music/article/b-o-b-alive-at-five-albany-22309982.php",
        "source_url": "https://www.timesunion.com/music/article/b-o-b-alive-at-five-albany-22309982.php",
        "description": "Free Alive at Five concert featuring DJ TGIF, Soular Sounds and Afrellie.",
        "duration_minutes": 180,
        "tags": ["free", "concert", "albany", "afrobeats"]
    },
    {
        "id": "event-fence-2026-reception-2026-06-26",
        "name": "Fence 2026 Opening Reception",
        "title": "Fence 2026 Opening Reception",
        "category": "art",
        "date": "2026-06-26T18:00:00+00:00",
        "time": "18:00",
        "venue": "The Arts Center of the Capital Region",
        "location": "The Arts Center of the Capital Region, Troy, NY",
        "coordinates": {"lat": 42.7284, "lng": -73.6918},
        "url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "source_url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "description": "Opening reception for Fence 2026, a juried show at The Arts Center.",
        "duration_minutes": 120,
        "tags": ["art", "opening", "troy"]
    },
    {
        "id": "event-job-adirondack-theatre-festival-2026-06-26",
        "name": "Adirondack Theatre Festival: Job",
        "title": "Adirondack Theatre Festival: Job",
        "category": "art",
        "date": "2026-06-26T19:30:00+00:00",
        "time": "19:30",
        "venue": "Charles R. Wood Theater",
        "location": "Charles R. Wood Theater, Glens Falls, NY",
        "coordinates": {"lat": 43.3095, "lng": -73.6440},
        "url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "source_url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "description": "Adirondack Theatre Festival production of Max Wolf Friedlich's psychological thriller Job.",
        "duration_minutes": 120,
        "tags": ["theater", "glens falls"]
    },
    {
        "id": "event-albany-institute-blanche-lazzell-2026-06-27",
        "name": "Blanche Lazzell: Becoming an American Modernist",
        "title": "Blanche Lazzell: Becoming an American Modernist",
        "category": "art",
        "date": "2026-06-27T10:00:00+00:00",
        "time": "10:00",
        "venue": "Albany Institute of History & Art",
        "location": "Albany Institute of History & Art, Albany, NY",
        "coordinates": {"lat": 42.6526, "lng": -73.7562},
        "url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "source_url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "description": "Albany Institute exhibition surveying Blanche Lazzell's modernist work.",
        "duration_minutes": 120,
        "tags": ["museum", "exhibition", "albany"]
    },
    {
        "id": "event-fence-2026-exhibition-2026-06-27",
        "name": "Fence 2026 Exhibition",
        "title": "Fence 2026 Exhibition",
        "category": "art",
        "date": "2026-06-27T12:00:00+00:00",
        "time": "12:00",
        "venue": "The Arts Center of the Capital Region",
        "location": "The Arts Center of the Capital Region, Troy, NY",
        "coordinates": {"lat": 42.7284, "lng": -73.6918},
        "url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "source_url": "https://www.timesunion.com/preview/article/events-albany-area-les-claypool-capital-pride-22297802.php",
        "description": "Fence 2026 juried exhibition, on view through July 24.",
        "duration_minutes": 90,
        "tags": ["art", "gallery", "troy"]
    },
    {
        "id": "event-nycb-innovators-icons-spac-2026-07-08",
        "name": "New York City Ballet: Innovators & Icons",
        "title": "New York City Ballet: Innovators & Icons",
        "category": "art",
        "date": "2026-07-08T19:30:00+00:00",
        "time": "19:30",
        "venue": "Saratoga Performing Arts Center",
        "location": "Saratoga Performing Arts Center, Saratoga Springs, NY",
        "coordinates": {"lat": 43.0554, "lng": -73.8059},
        "url": "https://www.timesunion.com/theater/article/new-york-city-ballet-brings-new-tiler-peck-work-21349620.php",
        "source_url": "https://www.timesunion.com/theater/article/new-york-city-ballet-brings-new-tiler-peck-work-21349620.php",
        "description": "NYCB program with a Tiler Peck world premiere, Balanchine and Robbins.",
        "duration_minutes": 150,
        "tags": ["ballet", "spac", "saratoga"]
    },
    {
        "id": "event-nycb-midsummer-spac-2026-07-09",
        "name": "New York City Ballet: A Midsummer Night's Dream",
        "title": "New York City Ballet: A Midsummer Night's Dream",
        "category": "art",
        "date": "2026-07-09T19:30:00+00:00",
        "time": "19:30",
        "venue": "Saratoga Performing Arts Center",
        "location": "Saratoga Performing Arts Center, Saratoga Springs, NY",
        "coordinates": {"lat": 43.0554, "lng": -73.8059},
        "url": "https://www.timesunion.com/theater/article/new-york-city-ballet-brings-new-tiler-peck-work-21349620.php",
        "source_url": "https://www.timesunion.com/theater/article/new-york-city-ballet-brings-new-tiler-peck-work-21349620.php",
        "description": "NYCB revives Balanchine's full-length A Midsummer Night's Dream at SPAC.",
        "duration_minutes": 150,
        "tags": ["ballet", "spac", "saratoga"]
    },
    {
        "id": "event-cms-dvorak-spac-2026-07-12",
        "name": "Chamber Music Society: Dvorak Quintet",
        "title": "Chamber Music Society: Dvorak Quintet",
        "category": "live music",
        "date": "2026-07-12T19:00:00+00:00",
        "time": "19:00",
        "venue": "Arthur Zankel Music Center",
        "location": "Arthur Zankel Music Center, Saratoga Springs, NY",
        "coordinates": {"lat": 43.0963, "lng": -73.7860},
        "url": "https://www.timesunion.com/music/article/spac-announces-lincoln-center-summer-season-21199168.php",
        "source_url": "https://www.timesunion.com/music/article/spac-announces-lincoln-center-summer-season-21199168.php",
        "description": "Opening program of the Chamber Music Society of Lincoln Center's SPAC summer residency.",
        "duration_minutes": 120,
        "tags": ["classical", "saratoga", "skidmore"]
    },
    {
        "id": "event-train-barenaked-ladies-spac-2026-07-22",
        "name": "Train and Barenaked Ladies",
        "title": "Train and Barenaked Ladies",
        "category": "live music",
        "date": "2026-07-22T19:00:00+00:00",
        "time": "19:00",
        "venue": "Saratoga Performing Arts Center",
        "location": "Saratoga Performing Arts Center, Saratoga Springs, NY",
        "coordinates": {"lat": 43.0554, "lng": -73.8059},
        "url": "https://www.timesunion.com/music/article/train-barenaked-ladies-tour-saratoga-2026-21152353.php",
        "source_url": "https://www.timesunion.com/music/article/train-barenaked-ladies-tour-saratoga-2026-21152353.php",
        "description": "Train and Barenaked Ladies co-headline the Drops of Jupiter anniversary tour at SPAC.",
        "duration_minutes": 180,
        "tags": ["concert", "spac", "saratoga"]
    },
    {
        "id": "event-guns-n-roses-spac-2026-07-26",
        "name": "Guns N' Roses at SPAC",
        "title": "Guns N' Roses at SPAC",
        "category": "live music",
        "date": "2026-07-26T19:00:00+00:00",
        "time": "19:00",
        "venue": "Saratoga Performing Arts Center",
        "location": "Saratoga Performing Arts Center, Saratoga Springs, NY",
        "coordinates": {"lat": 43.0554, "lng": -73.8059},
        "url": "https://www.timesunion.com/music/article/guns-n-roses-bring-world-tour-spac-2026-21204762.php",
        "source_url": "https://www.timesunion.com/music/article/guns-n-roses-bring-world-tour-spac-2026-21204762.php",
        "description": "Guns N' Roses bring their world tour to Saratoga Performing Arts Center.",
        "duration_minutes": 180,
        "tags": ["concert", "rock", "spac", "saratoga"]
    },
]


def get_events_json() -> str:
    """Get events data as JSON string."""
    return json.dumps(EVENTS_DATA, indent=2)


def main():
    """Generate real data JSON strings for environment variables."""
    
    # Get JSON strings
    restaurants_json = get_restaurants_json()
    events_json = get_events_json()
    
    print("=" * 80)
    print("RESTAURANTS JSON DATA")
    print("=" * 80)
    print(restaurants_json)
    print()
    
    print("=" * 80)
    print("EVENTS JSON DATA")
    print("=" * 80)
    print(events_json)
    print()
    
    print("=" * 80)
    print("TO USE THIS DATA:")
    print("=" * 80)
    print("Export the data as environment variables:")
    print("export AI_RESTAURANTS_DATA='<restaurants_json>'")
    print("export AI_EVENTS_DATA='<events_json>'")
    print()
    print("Then run: python -m happenstance.cli aggregate")


if __name__ == "__main__":
    main()
